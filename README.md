# Kochi Metro Induction Planner (Streamlit)

A Streamlit app for Kochi Metro train induction planning. Upload train, job card, and cleaning CSVs. Filters out ineligible trains, assigns service/standby roles, and visualizes results in color-coded tables and interactive scatter plots. Includes scenario editing, export, and robust rule-based logic for operational decision-making.

## Features
- Upload and process trainsets, job card, and cleaning slot data (CSV)
- Logic filters out trains with expired fitness/open job cards and considers cleaning capacity
- Prioritizes trains needing branding and with lower mileage
- Configurable parameters for service/standby train counts
- Table and graph visualizations of assignments
- What-if simulation—edit data and instantly see results
- Export induction plan as CSV

## Usage
1. Install requirements:  
   `pip install streamlit pandas matplotlib`
2. Run the Streamlit app:  
   `streamlit run streamlit_induction_app.py`
3. Upload your CSV inputs as prompted.

## License
MIT License
