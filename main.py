import streamlit as st
import pandas as pd
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime
import numpy as np
import altair as alt


def plot_payout_amount_by_month(df) -> None:
    st.subheader("Payout by month")

    df_2021 = df[df['createdAt'].dt.year == 2021]
    df_2022 = df[df['createdAt'].dt.year == 2022]
    payout_by_month_2021 = df_2021.groupby([df['createdAt'].dt.month]).agg(sum_payout = ('payoutAmount' , 'sum'))
    payout_by_month_2022 = df_2022.groupby([df['createdAt'].dt.month]).agg(sum_payout = ('payoutAmount' , 'sum'))
    payout_by_month_2021.index = "2021-" + payout_by_month_2021.index.astype(str)
    payout_by_month_2021.index = pd.to_datetime(payout_by_month_2021.index)
    payout_by_month_2022.index = "2022-" + payout_by_month_2022.index.astype(str)
    payout_by_month_2022.index = pd.to_datetime(payout_by_month_2022.index)
    payout_by_month_all = pd.concat([payout_by_month_2021, payout_by_month_2022], axis=0)
    st.line_chart(data=payout_by_month_all)


def plot_kpis(df) -> None:
    st.subheader("KPIs")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Amount", value="USD %.2f" % df.totalAmount.sum())
    col2.metric(label="Payout Amount", value="USD %.2f" % df.payoutAmount.sum())
    style_metric_cards(border_left_color = '#1a0a91')


def get_filtered_df(df, dates, apis, names) -> pd.DataFrame:
    from_date = np.datetime64(dates[0])
    to_date = np.datetime64(dates[1])
    df.createdAt = pd.to_datetime(df.createdAt).dt.tz_localize(None)
    newdf = df[(df.createdAt >= from_date)]
    # filter by api name
    if len(apis)>0:
        newdf = newdf[newdf['api.name'].isin(apis)]

    # filter by customer name
    if len(names)>0:
        newdf = newdf[newdf['name'].isin(names)]

    newdf = newdf[(newdf.createdAt <= to_date)]
    return newdf


def format_input_file(file) -> pd.DataFrame:
    try:
        df = pd.read_json(file)
    except ValueError:
        st.error("Please upload a valid JSON file")
        return
    else:
        subscription_df = pd.json_normalize(df.subscription)
        subscription_df = subscription_df.drop(columns=['__typename'])
        entity_df = pd.json_normalize(df.entity)
        entity_df = entity_df.drop(columns=["__typename"])
        a = df.drop(columns=['subscription', "entity"])
        b = pd.concat([a, subscription_df, entity_df], axis=1)
        b.createdAt = pd.to_datetime(b.createdAt)

        # Check if na
        b.name = b.name.fillna("undefined")

        return b


def plot_api_groups(df):
    st.subheader("Payout by API endpoint")
    grouped_df = df.groupby("api.name").sum()
    grouped_df = grouped_df.drop(columns=["id", "totalAmount", "paid", "paidout", "additionalAmount", "refunded", "refundedAmount", "billingPlanVersion.price"])
    grouped_df["endpoint"] = grouped_df.index
    st.bar_chart(grouped_df, x="endpoint", y="payoutAmount")


def plot_payout_amount_by_client(df):
    st.subheader("Payout by customer")
    grouped_df = df.groupby("name").sum()
    grouped_df = grouped_df.sort_values(by="payoutAmount", ascending=False)
    grouped_df["client"] = grouped_df.index

    #st.bar_chart(grouped_df, y="payoutAmount")
    c = alt.Chart(grouped_df).mark_bar().encode(
        x=alt.X('client', sort=None),
        y='payoutAmount',
    )

    st.altair_chart(c, use_container_width=True)


def main():
    st.set_page_config(
        layout="wide",
        page_title="RapidAPI Insights",
        page_icon="https://developer.symanto.com/favicon.ico",
    )

    st.header("RapidAPI Insights")
    file = st.file_uploader("Upload your json file here")
    if file:
        df = format_input_file(file)
        if df is None:
            return

        with st.sidebar:
            st.subheader("Filter section")

            api_name_filter = st.multiselect(
                'Filter by API endpoint',
                list(dict.fromkeys(df["api.name"].values)))

            customer_name = st.multiselect(
                "Filter by customer",
                list(dict.fromkeys(df["name"].values)))

            date_filter = st.slider(
                "Filter by time range",
                value=(datetime(df.createdAt.min().year, df.createdAt.min().month, df.createdAt.min().day), datetime(df.createdAt.max().year, df.createdAt.max().month, df.createdAt.max().day)))

        df = get_filtered_df(df, date_filter, api_name_filter, customer_name)

        plot_kpis(df)

        plot_api_groups(df)
        plot_payout_amount_by_client(df)
        plot_payout_amount_by_month(df)

        st.subheader("Raw filtered output")
        st.write(df)

        # Export
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered data",
            csv,
            "file.csv",
            "text/csv",
            key='download-csv'
        )


if __name__ == '__main__':
    main()
