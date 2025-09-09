# 🪑 Seat Allocation Solver

Seat Allocation Solver is a tool designed to optimize and automate the
allocation of subteams into available bays using **Mixed Integer Linear
Programming (MILP)**.\
It ensures optimal seat distribution while respecting constraints such
as bay capacity, minimum attendance, and at least one full-attendance
day per subteam.

------------------------------------------------------------------------

## 🚀 Features

-   Automatic seat allocation using MILP optimization.
-   Handles subteam preferences and attendance requirements.
-   Ensures bay capacity constraints are always satisfied.
-   Provides flexibility for shared bay usage among multiple subteams.
-   Simple Streamlit web interface for easy usage.

------------------------------------------------------------------------

## 🛠️ Tech Stack

-   **Python**
-   **Pandas** for data handling
-   **PuLP** for MILP optimization
-   **Streamlit** for UI

------------------------------------------------------------------------

## 📂 Project Structure

    Seat-allocation-solver/
    │── app.py                # Streamlit frontend
    │── solver.py             # Core solver implementation
    │── requirements.txt      # Python dependencies
    │── sample_data/          # Example input files
    │── README.md             # Project documentation

------------------------------------------------------------------------

## 📊 Input Files

1.  **subteams.csv**
    -   Contains information about subteams and attendance.
2.  **bays.csv**
    -   Contains information about bays and their seating capacity.

------------------------------------------------------------------------

## ▶️ How to Run

### 1. Clone the Repository

``` bash
git clone https://github.com/Mandil-18/Seat-allocation-solver.git
cd Seat-allocation-solver
```

### 2. Create and Activate Virtual Environment

**Mac/Linux:**

``` bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

``` bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

``` bash
pip install -r requirements.txt
```

### 4. Run the Streamlit App

``` bash
streamlit run app.py
```

------------------------------------------------------------------------

## 📷 Screenshots

<img width="1669" height="535" alt="image" src="https://github.com/user-attachments/assets/a6c1f5a4-7a5a-4691-bee8-1ee6ee6aa7da" />


------------------------------------------------------------------------

## 🤝 Contributing

Contributions are welcome!\
Feel free to fork the repo and submit pull requests.

------------------------------------------------------------------------

## 📜 License

This project is licensed under the MIT License.
