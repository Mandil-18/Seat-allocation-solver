import pandas as pd
import pulp
from collections import defaultdict

# ----------------------------
# CONSTANTS
# ----------------------------
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DAYS_REQUIRED = 3
SPLIT_PENALTY = 1.0
ATTEND_PENALTY = 1000.0


# ----------------------------
# MILP SOLVER
# ----------------------------
def solve_milp(subteams_df: pd.DataFrame, bays_df: pd.DataFrame,
               days_required: int = DAYS_REQUIRED,
               split_penalty: float = SPLIT_PENALTY,
               attend_penalty: float = ATTEND_PENALTY,
               debug: bool = False):
    # Sanitize inputs
    subteams_df = subteams_df.apply(pd.to_numeric, errors="ignore")
    bays_df = bays_df.apply(pd.to_numeric, errors="ignore")

    subteams = subteams_df.index.tolist()
    bays = bays_df.index.tolist()

    # Model
    model = pulp.LpProblem("Seat_Allocation_SoftAttendance", pulp.LpMinimize)

    # Variables
    x = pulp.LpVariable.dicts("x", (subteams, DAYS), cat="Binary")
    assign = pulp.LpVariable.dicts("assign", (subteams, bays, DAYS), lowBound=0, cat="Integer")
    y = pulp.LpVariable.dicts("y", (subteams, bays, DAYS), cat="Binary")
    splits = pulp.LpVariable.dicts("splits", (subteams, DAYS), lowBound=0, cat="Integer")
    z = pulp.LpVariable.dicts("z", (subteams, bays, DAYS), cat="Binary")
    attend_short = pulp.LpVariable.dicts("attend_short", subteams, lowBound=0, cat="Integer")

    # Constraints
    for s in subteams:
        M_s = int(subteams_df.loc[s, "Members"])
        model += pulp.lpSum(x[s][d] for d in DAYS) + attend_short[s] >= days_required
        for d in DAYS:
            model += pulp.lpSum(assign[s][b][d] for b in bays) == M_s * x[s][d]

    for b in bays:
        cap_b = int(bays_df.loc[b, "Capacity"])
        for d in DAYS:
            model += pulp.lpSum(assign[s][b][d] for s in subteams) <= cap_b

    for s in subteams:
        M_s = int(subteams_df.loc[s, "Members"])
        for b in bays:
            cap_b = int(bays_df.loc[b, "Capacity"])
            for d in DAYS:
                model += assign[s][b][d] <= cap_b * y[s][b][d]
                model += assign[s][b][d] >= 1 * y[s][b][d]
                model += assign[s][b][d] <= M_s * x[s][d]

    for s in subteams:
        for d in DAYS:
            model += splits[s][d] >= pulp.lpSum(y[s][b][d] for b in bays) - 1

    for s in subteams:
        M_s = int(subteams_df.loc[s, "Members"])
        for b in bays:
            for d in DAYS:
                model += assign[s][b][d] >= M_s * z[s][b][d]
                model += z[s][b][d] <= y[s][b][d]

    for s in subteams:
        model += pulp.lpSum(x[s][d] for d in DAYS) >= 1
        model += attend_short[s] <= days_required

    # Objective
    model += (
        pulp.lpSum(y[s][b][d] for s in subteams for b in bays for d in DAYS)
        + split_penalty * pulp.lpSum(splits[s][d] for s in subteams for d in DAYS)
        + attend_penalty * pulp.lpSum(attend_short[s] for s in subteams)
    )

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=120)
    status = model.solve(solver)
    status_str = pulp.LpStatus[status]

    # Build solution
    def build_solution_from_model():
        schedule_rows, expanded_rows = [], []
        for s in subteams:
            M_s = int(subteams_df.loc[s, "Members"])
            present_days = [d for d in DAYS if pulp.value(x[s][d]) >= 0.5]
            day_map = {}
            for d in present_days:
                bays_assigned = []
                for b in bays:
                    val = int(round(pulp.value(assign[s][b][d]) or 0))
                    if val > 0:
                        bays_assigned.append({"Bay": b, "Assigned": val})
                        expanded_rows.append({
                            "Subteam": s,
                            "Team": subteams_df.loc[s, "Team"],
                            "Day": d,
                            "Shift": subteams_df.loc[s, "Shift-timing"],
                            "Bay": b,
                            "SeatsAllocated": val,
                        })
                day_map[d] = bays_assigned
            schedule_rows.append({
                "Subteam": s,
                "Team": subteams_df.loc[s, "Team"],
                "Members": M_s,
                "Shift": subteams_df.loc[s, "Shift-timing"],
                "Days_present": ", ".join(present_days),
                "Assignments_by_day": day_map,
                "Attend_short": int(round(pulp.value(attend_short[s] or 0)))
            })

        summary = pd.DataFrame(schedule_rows).set_index("Subteam")
        expanded = pd.DataFrame(expanded_rows)
        return summary, expanded

    if status_str == "Optimal":
        return build_solution_from_model()
    else:
        return greedy_scheduler_force3(subteams_df, bays_df, DAYS)


# ----------------------------
# GREEDY FALLBACK
# ----------------------------
def greedy_scheduler_force3(sub_df, bays_df, DAYS):
    subteams = sub_df.index.tolist()
    bays = bays_df.index.tolist()

    rem_cap = {(b, d): int(bays_df.loc[b, "Capacity"]) for b in bays for d in DAYS}
    assign_res = defaultdict(int)
    x_res = {(s, d): 0 for s in subteams for d in DAYS}

    order = sorted(subteams, key=lambda s: int(sub_df.loc[s, "Members"]), reverse=True)

    for s in order:
        M_s = int(sub_df.loc[s, "Members"])
        day_caps = {d: sum(rem_cap[(b, d)] for b in bays) for d in DAYS}
        feasible_days = [d for d in DAYS if day_caps[d] >= M_s]
        full_day = max(feasible_days, key=lambda d: day_caps[d]) if feasible_days else max(day_caps.items(), key=lambda kv: kv[1])[0]

        needed = M_s
        for b in sorted(bays, key=lambda b: rem_cap[(b, full_day)], reverse=True):
            if needed <= 0:
                break
            take = min(rem_cap[(b, full_day)], needed)
            if take > 0:
                assign_res[(s, b, full_day)] += take
                rem_cap[(b, full_day)] -= take
                needed -= take
        if needed > 0:
            raise RuntimeError(f"Greedy couldn't place full meeting for {s} on {full_day}")
        x_res[(s, full_day)] = 1

        days_to_assign = DAYS_REQUIRED - 1
        for _ in range(days_to_assign):
            day_caps = {d: sum(rem_cap[(b, d)] for b in bays) for d in DAYS}
            candidate_days = sorted(DAYS, key=lambda d: (-day_caps[d], d))
            for best_day in candidate_days:
                if best_day == full_day and len(candidate_days) > 1:
                    continue
                needed = M_s
                for b in sorted(bays, key=lambda b: rem_cap[(b, best_day)], reverse=True):
                    if needed <= 0:
                        break
                    take = min(rem_cap[(b, best_day)], needed)
                    if take > 0:
                        assign_res[(s, b, best_day)] += take
                        rem_cap[(b, best_day)] -= take
                        needed -= take
                if needed == 0:
                    x_res[(s, best_day)] = 1
                    break
            else:
                raise RuntimeError(f"Greedy couldn't place day for {s}.")

    expanded_rows, schedule_rows = [], []
    for s in subteams:
        M_s = int(sub_df.loc[s, "Members"])
        present_days = [d for d in DAYS if x_res[(s, d)] == 1]
        day_map = {}
        for d in present_days:
            bays_assigned = []
            for b in bays:
                val = assign_res[(s, b, d)]
                if val > 0:
                    bays_assigned.append({"Bay": b, "Assigned": val})
                    expanded_rows.append({
                        "Subteam": s,
                        "Team": sub_df.loc[s, "Team"],
                        "Day": d,
                        "Shift": sub_df.loc[s, "Shift-timing"],
                        "Bay": b,
                        "SeatsAllocated": val,
                    })
            day_map[d] = bays_assigned
        schedule_rows.append({
            "Subteam": s,
            "Team": sub_df.loc[s, "Team"],
            "Members": M_s,
            "Shift": sub_df.loc[s, "Shift-timing"],
            "Days_present": ", ".join(present_days),
            "Assignments_by_day": day_map,
        })

    summary = pd.DataFrame(schedule_rows).set_index("Subteam")
    expanded = pd.DataFrame(expanded_rows)
    return summary, expanded


# ----------------------------
# PUBLIC ENTRY
# ----------------------------
def solve(subteams_df: pd.DataFrame, bays_df: pd.DataFrame, method="milp"):
    if method == "milp":
        return solve_milp(subteams_df, bays_df)
    elif method == "greedy":
        return greedy_scheduler_force3(subteams_df, bays_df, DAYS)
    else:
        raise ValueError("Unknown method. Use 'milp' or 'greedy'.")
