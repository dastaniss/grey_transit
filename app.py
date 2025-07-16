import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile

# login procedure
# This is a simple login mechanism for demonstration purposes.
USER_CREDENTIALS = {
    "ktzh": "ktzhpass"
}

def login():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if USER_CREDENTIALS.get(username) == password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid username or password")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Grey Transit')
    output.seek(0)
    return output

def read_single_csv_from_zip(uploaded_file):
    with zipfile.ZipFile(uploaded_file) as z:
        # Get list of files that are not hidden/macOS junk
        valid_files = [f for f in z.namelist() if f.endswith('.csv') and '__MACOSX' not in f and not f.startswith('.')]
        if len(valid_files) != 1:
            raise ValueError(f"Expected 1 CSV file, found {len(valid_files)}: {valid_files}")
        return pd.read_csv(z.open(valid_files[0]))

st.set_page_config(page_title="Grey Transit Matcher", layout="wide")
st.title("Grey Transit Matcher")

st.subheader("1. Upload Import and Export `.csv.zip` Files")

# Upload zipped import files
import_file = st.file_uploader("Upload Import File Q1 (.csv.zip)", type="zip", key="import_file")

# Upload zipped export files
export_file = st.file_uploader("Upload Export File Q1 (.csv.zip)", type="zip", key="export_file")

# Proceed if all files are uploaded
if all([import_file, export_file]):

    # Read zipped CSVs
    export_df = read_single_csv_from_zip(export_file)
    import_df = read_single_csv_from_zip(import_file)

    # Intersection and concat for export
    # common_columns_ex = ex_10_df.columns.intersection(ex_11_df.columns).intersection(ex_12_df.columns)
    # export_all = pd.concat([ex_10_df[common_columns_ex], ex_11_df[common_columns_ex], ex_12_df[common_columns_ex]], ignore_index=True)

    # # Intersection and concat for import
    # common_columns_im = im_10_df.columns.intersection(im_11_df.columns).intersection(im_12_df.columns)
    # import_all = pd.concat([im_10_df[common_columns_im], im_11_df[common_columns_im], im_12_df[common_columns_im]], ignore_index=True)

    # --- Continue previous transformation ---


    # import_df = import_df[import_df['Наименование ГП'].notna()]
    # export_df = export_df[export_df['Наименование ГП'].notna()]
    # import_df["Наименование ГП"] = import_df["Наименование ГП"].apply(lambda x: x.replace('ТОВАРИЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "QAZEXPOCENTRE - PIPE"', 'ТОО "QAZEXPOCENTRE - PIPE"'))
    # export_df["Наименование ГП"] = export_df["Наименование ГП"].apply(lambda x: x.replace('ТОВАРИЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "QAZEXPOCENTRE - PIPE"', 'ТОО "QAZEXPOCENTRE - PIPE"'))

#----------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------FROM HERE----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------
    import_df.rename(columns={"Вес на вагон (кг)": "Вес на вагон (кг)_x",
                                "Код груза": "Код груза_x",
                                "Номер вагона\\конт": "Номер вагона",
                                "Наименование станции назнаения": "Наименование станции назначения"}, inplace=True)

    export_df.rename(columns={"Вес на вагон (кг)": "Вес на вагон (кг)_y",
                                "Код груза": "Код груза_y",
                                "Номер вагона\\конт": "Номер вагона"}, inplace = True)


    import_df = import_df[['Документ', 'Наименование ГО', 'Наименование ГП', 'Наименование страны отправления',
                            "Наименование станции отправления", "Станция отправления", "Наименование страны назначения",
                            "Наименование станции назначения", 'Станция назначения', "Номер вагона",
                            'Общий вес по документу (кг)', 'Вес на вагон (кг)_x', 'Код груза_x', 'Наименование груза',
                            'Код грузополучателя', 'Дата прибытия', 'Взыскано по прибытию (последние 2 знака тиыны)']]

    export_df = export_df[['Документ', "Наименование ГО", "Наименование ГП", 'Наименование страны отправления',
                            "Наименование станции отправления", "Станция отправления", "Наименование страны назначения",
                            "Наименование станции назначения", 'Станция назначения', "Номер вагона",
                            'Общий вес по документу (кг)', 'Вес на вагон (кг)_y', 'Код груза_y', 'Наименование груза',
                            'Код грузоотправителя', 'Дата отправления',
                            'Взыскано при отправления  (последние 2 знака тиыны)']]



    import_df['Дата прибытия'] = pd.to_datetime(import_df['Дата прибытия'], dayfirst=True, errors='coerce')
    export_df['Дата отправления'] = pd.to_datetime(export_df['Дата отправления'], dayfirst=True, errors='coerce')

    merged = pd.merge(
        import_df,
        export_df,
        left_on=['Номер вагона', "Код груза_x"],#, 'Наименование ГП', 'Станция назначения', "Вес на вагон (кг)_x"],
        right_on=['Номер вагона', "Код груза_y"],#, 'Наименование ГО', 'Станция отправления', "Вес на вагон (кг)_y"],
        how='inner'
    )

    merged = merged[merged['Наименование страны отправления_x'] != merged['Наименование страны назначения_y']]
    merged = merged[merged['Дата прибытия'] <= merged['Дата отправления']]
    merged = merged[merged["Вес на вагон (кг)_x"] != 0]

    grey_transit_wagons = merged.copy().reset_index(drop=True)

    grey_transit_wagons_1 = grey_transit_wagons[
        (grey_transit_wagons["Наименование ГП_x"] == grey_transit_wagons["Наименование ГО_y"]) | 
        (grey_transit_wagons["Станция назначения_x"] == grey_transit_wagons["Станция отправления_y"]) | 
        (grey_transit_wagons["Вес на вагон (кг)_x"] == grey_transit_wagons["Вес на вагон (кг)_y"])] 

    grey_transit_wagons_2 = grey_transit_wagons[
        ((grey_transit_wagons["Наименование ГП_x"] == grey_transit_wagons["Наименование ГО_y"]) &  (grey_transit_wagons["Станция назначения_x"] == grey_transit_wagons["Станция отправления_y"])) |
        ((grey_transit_wagons["Наименование ГП_x"] == grey_transit_wagons["Наименование ГО_y"]) &  (grey_transit_wagons["Вес на вагон (кг)_x"] == grey_transit_wagons["Вес на вагон (кг)_y"])) |
        ((grey_transit_wagons["Станция назначения_x"] == grey_transit_wagons["Станция отправления_y"]) & (grey_transit_wagons["Вес на вагон (кг)_x"] == grey_transit_wagons["Вес на вагон (кг)_y"]))]

    grey_transit_wagons_3 = grey_transit_wagons[
        (grey_transit_wagons["Наименование ГП_x"] == grey_transit_wagons["Наименование ГО_y"]) &
        (grey_transit_wagons["Станция назначения_x"] == grey_transit_wagons["Станция отправления_y"]) &
        (grey_transit_wagons["Вес на вагон (кг)_x"] == grey_transit_wagons["Вес на вагон (кг)_y"])].reset_index(drop=True)
    

    filter_2 = grey_transit_wagons_2.merge(grey_transit_wagons_3, how = "left", indicator=True)
    filter_2 = filter_2[filter_2['_merge'] == 'left_only'].drop(columns=['_merge']).reset_index(drop=True)

    filter_1 = grey_transit_wagons_1.merge(grey_transit_wagons_2, how = "left", indicator=True)
    filter_1 = filter_1[filter_1['_merge'] == 'left_only'].drop(columns=['_merge']).reset_index(drop=True)

    filter_0 = grey_transit_wagons.merge(grey_transit_wagons_1, how = "left", indicator=True)
    filter_0 = filter_0[filter_0['_merge'] == 'left_only'].drop(columns=['_merge']).reset_index(drop=True)
    
#----------------------------------------------------------------------------------------------------------------------------------------
#---------------------------------TO HERE------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------

    st.success(f"Successfully matched")

    # grey_transit_wagons_3 = pd.read_csv("filtered_all.csv", index=False)
    # filter_2 = pd.read_csv("filtered_2.csv", index=False)
    # filter_1 = pd.read_csv("filtered_1.csv", index=False)
    # filter_0 = pd.read_csv("filtered_0.csv", index=False)

    st.markdown(
    f'<h3 style="color:#FF0000;">Совподение по Номеру вагона, Коду груза + Грузо-получатель/отправитель, Станция назначения/отправления, Вес вагона</h3>',
    unsafe_allow_html=True)
    st.markdown(
    f'<h3 style="color:#FF0000;">Количество кандидатов: {len(grey_transit_wagons_3)}</h3>',
    unsafe_allow_html=True)

    st.dataframe(grey_transit_wagons_3, use_container_width=True)
    excel_file = convert_df_to_excel(grey_transit_wagons_3)
    st.download_button(
        label="Download Excel",
        data=excel_file,
        file_name="high_prob.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown(
    f'<h3 style="color:#FF4500;">Совпадение по Номеру вагона, Коду груза + 2 из 3 полей</h3>',
    unsafe_allow_html=True)
    st.markdown(
    f'<h3 style="color:#FF4500;">Количество кандидатов: {len(filter_2)}</h3>',
    unsafe_allow_html=True)


    st.dataframe(filter_2, use_container_width=True)
    excel_file = convert_df_to_excel(filter_2)
    st.download_button(
        label="Download Excel",
        data=excel_file,
        file_name="medium_high_prob.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown(
    f'<h3 style="color:#FFA500;">Совпадение по Номеру вагона, Коду груза + 1 из 3 полей</h3>',
    unsafe_allow_html=True)
    st.markdown(
    f'<h3 style="color:#FFA500;">Количество кандидатов: {len(filter_1)}</h3>',
    unsafe_allow_html=True)


    st.dataframe(filter_1, use_container_width=True)
    excel_file = convert_df_to_excel(filter_1)
    st.download_button(
        label="Download Excel",
        data=excel_file,
        file_name="medium_low_prob.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


    st.markdown(
    f'<h3 style="color:#FFFF00;">Совпадение по Номеру вагона и Коду груза</h3>',
    unsafe_allow_html=True)
    st.markdown(
    f'<h3 style="color:#FFFF00;">Количество кандидатов: {len(filter_0)}</h3>',
    unsafe_allow_html=True)


    st.dataframe(filter_0, use_container_width=True)
    excel_file = convert_df_to_excel(filter_0)
    st.download_button(
        label="Download Excel",
        data=excel_file,
        file_name="low_prob.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.info("Please upload files to continue.")
