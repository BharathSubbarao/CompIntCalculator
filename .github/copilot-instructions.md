# Project: Python Compound Interest Calculator (Web App)

## 🎯 Role
You are an expert Python developer specializing in clean, mathematical web applications. Your goal is to build a high-performance, single-page compound interest calculator.

## 🛠 Tech Stack
- **Language**: Python 3.10+
- **Web Framework**: Streamlit (Preferred for rapid single-page apps)
- **Data Visualization**: Plotly (For interactive charts)
- **Formatting**: PEP 8 standards

## 🏗 Project Structure
- `app.py`: Main application file containing the logic and UI.
- `requirements.txt`: Project dependencies.
- `README.md`: Human-readable setup instructions.

## 📋 Core Features & Logic
1. **User Inputs**:
   - Principal Amount ($P$)
   - Monthly Contribution (optional) ($C$)
   - Annual Interest Rate ($r$ in %)
   - Time ($t$ in years)
   - Compounding Frequency ($n$, e.g., Monthly, Quarterly, Annually)
2. **Formula**: 
   - $A = P(1 + r/n)^{nt} + C \frac{(1 + r/n)^{nt} - 1}{r/n}$
3. **Visuals**:
   - A dynamic line chart showing growth over time.
   - A summary table showing year-over-year balance.
4. **Summary Metrics**:
   - Total Future Value ($A$)
   - Total Interest Earned ($A - P - C \cdot t$)
5. **Currency**:
   - Default currency is INR, but allow users to select from a dropdown (e.g., USD, EUR, GBP, JPY).
   - Display all monetary values with the appropriate currency symbol.
   - Display INR values with the '₹' symbol, USD with '$', EUR with '€', GBP with '£', and JPY with '¥'.
   - Display all monetary values with two decimal places for consistency and clarity.
   - Display all monetary values in INR with comma separators in Indian style (e.g., 1,00,000.00 for one lakh) and in international style for other currencies (e.g., 100,000.00 for one hundred thousand).

## 🎨 UI & Styling
- **Default State**: Set the default theme to match the user's system settings.


## ⚠️ Boundaries & Rules
- **Modern Syntax**: Use type hinting for all functions.
- **Error Handling**: Validate that inputs are non-negative.
- **Clean UI**: Use a sidebar for inputs and the main area for results and graphs.
- **No Global Variables**: Encapsulate logic within functions.
- **Currency Variables**: All variable names for currency must start with the prefix 'money_'.


## 🚀 Commands
- **Install**: `pip3 install streamlit plotly`
- **Run**: `python3 -m streamlit run app.py`
