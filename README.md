# Smart-Data-Insight-Web-App
# 🧠 AI-Powered Data Analysis Web Platform

An interactive Streamlit web application that allows users to upload CSV/Excel files, explore datasets, compute KPIs, and receive automatic insights using artificial intelligence (OpenAI).

## 🚀 Features

- 📁 **File upload & management**:
  - Upload multiple CSV files
  - View history of uploaded files
- 📊 **Automatic KPI computation**:
  - Number of rows/columns
  - Missing values per column
- 🧹 **Data cleaning module**:
  - User-selectable NaN filling methods (mean, median, mode)
- 📈 **Data visualization**:
  - Histogram, boxplot, scatter plot
  - Pie chart for categorical data
  - Correlation heatmap
- 🤖 **AI interpretation**:
  - Generates natural language insights from sample rows
  - Detects column types, data patterns, and possible anomalies

## 🛠️ Tech Stack

- **Frontend & Backend**: [Streamlit](https://streamlit.io)
- **Database**: MongoDB
- **Data Handling**: Pandas
- **Authentication**: bcrypt, session state
- **AI Integration**: OpenAI API (gpt-4)
- **Visualizations**: Seaborn, Matplotlib

## 📂 Project Structure
```
Smart-Data-Insight-Web-App/
├── main.py # Main Streamlit app
├── requirements.txt # Python dependencies
├── uploads/ # Folder for user-uploaded CSV files

```
## 🔐 Setup & Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-username/Smart-Data-Insight-Web-App.git
cd Smart-Data-Insight-Web-App
```
Create a virtual environment

```bash

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
Install dependencies

```bash

pip install -r requirements.txt
```
Run the app
```
streamlit run app.py
```
