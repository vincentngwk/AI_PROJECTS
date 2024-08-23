import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

# Set page configuration
st.set_page_config(page_title="EDA App", layout="wide")

def auto_detect_type(series):
    if pd.api.types.is_numeric_dtype(series):
        return 'Numeric'
    elif pd.api.types.is_datetime64_any_dtype(series):
        return 'Date'
    else:
        try:
            pd.to_datetime(series)
            return 'Date'
        except (ValueError, TypeError):
            return 'Text'

def filter_dataframe(df, column, filter_type, value):
    if filter_type == "equals":
        return df[df[column] == value]
    elif filter_type == "greater than":
        return df[df[column] > value]
    elif filter_type == "less than":
        return df[df[column] < value]
    elif filter_type == "contains":
        return df[df[column].astype(str).str.contains(value, case=False)]
    return df

def create_wordcloud(df, text_column):
    text = ' '.join(df[text_column].astype(str))
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    # Convert WordCloud to image
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    # Convert matplotlib figure to plotly figure
    fig = px.imshow(wordcloud.to_array())
    fig.update_layout(
        xaxis={'showticklabels': False},
        yaxis={'showticklabels': False},
        hovermode='closest'
    )
    fig.update_traces(hoverinfo='none', hovertemplate=None)
    return fig

def create_visualization(df, viz_id):
    st.subheader(f"Visualization {viz_id}")
    
    # Data filtering for this visualization
    st.write("Filter data for this visualization:")
    filter_column = st.selectbox("Select column to filter", df.columns, key=f"filter_col_{viz_id}")
    filter_type = st.selectbox("Select filter type", ["equals", "greater than", "less than", "contains"], key=f"filter_type_{viz_id}")
    filter_value = st.text_input("Enter filter value", key=f"filter_value_{viz_id}")
    
    if filter_value:
        df = filter_dataframe(df, filter_column, filter_type, filter_value)

    viz_type = st.selectbox(f"Choose visualization type for Visualization {viz_id}", 
        ["Histogram", "Bar Chart", "Scatter Plot", "Box Plot", "Correlation Heatmap", "Pair Plot", "Time Series Plot", "Word Cloud"],
        key=f"viz_type_{viz_id}")

    if viz_type == "Histogram":
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if not numeric_cols.empty:
            col = st.selectbox("Select a column for the histogram", numeric_cols, key=f"hist_col_{viz_id}")
            color_scheme = st.color_picker("Choose a color", "#3366cc", key=f"hist_color_{viz_id}")
            fig = px.histogram(df, x=col, color_discrete_sequence=[color_scheme])
            fig.update_layout(autosize=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No numeric columns available for histogram.")

    elif viz_type == "Bar Chart":
        x_col = st.selectbox("Select X-axis column", df.columns, key=f"bar_x_{viz_id}")
        y_col = st.selectbox("Select Y-axis column", df.select_dtypes(include=['float64', 'int64']).columns, key=f"bar_y_{viz_id}")
        color_col = st.selectbox("Select color column (optional)", [None] + list(df.columns), key=f"bar_color_{viz_id}")
        fig = px.bar(df, x=x_col, y=y_col, color=color_col)
        fig.update_layout(autosize=True)
        st.plotly_chart(fig, use_container_width=True)

    elif viz_type == "Scatter Plot":
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) >= 2:
            x_col = st.selectbox("Select X-axis column", numeric_cols, key=f"scatter_x_{viz_id}")
            y_col = st.selectbox("Select Y-axis column", numeric_cols, key=f"scatter_y_{viz_id}")
            color_col = st.selectbox("Select color column (optional)", [None] + list(df.columns), key=f"scatter_color_{viz_id}")
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col)
            fig.update_layout(autosize=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("At least two numeric columns are required for a scatter plot.")

    elif viz_type == "Box Plot":
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if not numeric_cols.empty:
            y_col = st.selectbox("Select column for box plot", numeric_cols, key=f"box_y_{viz_id}")
            x_col = st.selectbox("Select grouping column (optional)", [None] + list(df.columns), key=f"box_x_{viz_id}")
            fig = px.box(df, y=y_col, x=x_col)
            fig.update_layout(autosize=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No numeric columns available for box plot.")

    elif viz_type == "Correlation Heatmap":
        numeric_df = df.select_dtypes(include=['float64', 'int64'])
        if not numeric_df.empty:
            fig = px.imshow(numeric_df.corr(), color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
            fig.update_layout(autosize=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No numeric columns available for correlation heatmap.")

    elif viz_type == "Pair Plot":
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) >= 2:
            cols = st.multiselect("Select columns for pair plot", numeric_cols, default=numeric_cols[:4].tolist(), key=f"pair_cols_{viz_id}")
            if len(cols) < 2:
                st.error("Please select at least two columns for the pair plot.")
            else:
                fig = px.scatter_matrix(df[cols])
                fig.update_layout(autosize=True)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("At least two numeric columns are required for a pair plot.")

    elif viz_type == "Time Series Plot":
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if date_cols and not numeric_cols.empty:
            date_col = st.selectbox("Select date column", date_cols, key=f"ts_date_{viz_id}")
            value_col = st.selectbox("Select value column", numeric_cols, key=f"ts_value_{viz_id}")
            fig = px.line(df, x=date_col, y=value_col)
            fig.update_layout(autosize=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Both date and numeric columns are required for a time series plot.")

    elif viz_type == "Word Cloud":
        text_cols = df.select_dtypes(include=['object']).columns
        if not text_cols.empty:
            text_col = st.selectbox("Select text column for word cloud", text_cols, key=f"wordcloud_col_{viz_id}")
            fig = create_wordcloud(df, text_col)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No text columns available for word cloud.")

def main():
    st.title("Exploratory Data Analysis App")
    st.write("Upload your CSV or Excel file to get started with interactive data analysis and visualization.")

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Auto-detect and select data types
            st.subheader("Data Type Selection")
            for col in df.columns:
                detected_type = auto_detect_type(df[col])
                data_types = {'Text': 'object', 'Numeric': 'float64', 'Integer': 'int64', 'Date': 'datetime64[ns]'}
                selected_type = st.selectbox(f"Select data type for '{col}' (Auto-detected: {detected_type})", 
                                             options=list(data_types.keys()), 
                                             index=list(data_types.keys()).index(detected_type),
                                             key=f"dtype_{col}")
                
                # Apply the selected data type
                if data_types[selected_type] == 'datetime64[ns]':
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                elif data_types[selected_type] in ['float64', 'int64']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                else:
                    df[col] = df[col].astype(str)

            # Date slicer in the sidebar
            st.sidebar.title("Date Slicer")
            date_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
            if date_columns:
                selected_date_column = st.sidebar.selectbox("Select date column for filtering", date_columns)
                date_min = df[selected_date_column].min().date()
                date_max = df[selected_date_column].max().date()
                selected_start_date, selected_end_date = st.sidebar.date_input(
                    "Select date range",
                    value=[date_min, date_max],
                    min_value=date_min,
                    max_value=date_max
                )
                df_filtered = df[(df[selected_date_column].dt.date >= selected_start_date) & 
                                 (df[selected_date_column].dt.date <= selected_end_date)]
            else:
                df_filtered = df
                st.sidebar.write("No date columns available for filtering.")

            # Display interactive data preview
            st.subheader("Data Preview")
            gb = GridOptionsBuilder.from_dataframe(df_filtered)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            gb.configure_side_bar()
            grid_options = gb.build()
            AgGrid(df_filtered, gridOptions=grid_options, enable_enterprise_modules=True, height=400, width='100%')

            # Visualizations
            if 'visualizations' not in st.session_state:
                st.session_state.visualizations = []

            # Display existing visualizations
            for viz in st.session_state.visualizations:
                create_visualization(df_filtered, viz)

            # Create new visualization button
            if st.button("Create New Visualization", key="create_new_viz"):
                new_viz_id = len(st.session_state.visualizations) + 1
                st.session_state.visualizations.append(new_viz_id)
                create_visualization(df_filtered, new_viz_id)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()