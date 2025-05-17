import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# 配置页面
st.set_page_config(page_title="订单管理系统", layout="wide")

# 数据库配置
DB = "orders.db"
os.makedirs("data", exist_ok=True)
DB_PATH = os.path.join("data", DB)

# 初始化数据库
def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        日期 TEXT,
        信保单号 TEXT,
        负责人 TEXT,
        客户名称 TEXT,
        国家 TEXT,
        产品名称 TEXT,
        件数 INTEGER,
        汇率 REAL,
        产品总价_美元 REAL,
        产品总价_元 REAL,
        计重 REAL,
        运费_美元 REAL,
        运费_元 REAL,
        物流 TEXT,
        物流费 REAL,
        备注 TEXT,
        订单状态 TEXT DEFAULT '排图',
        跟进备注 TEXT
    )
    """)
    conn.commit()
    conn.close()

create_table()

# 插入数据
def insert_order(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (
            日期, 信保单号, 负责人, 客户名称, 国家, 产品名称, 件数, 汇率,
            产品总价_美元, 产品总价_元, 计重, 运费_美元, 运费_元, 物流, 物流费, 备注
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

# 读取数据
def get_orders(filter_responsible=None, filter_status=None, keyword=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if filter_responsible:
        query += " AND 负责人 = ?"
        params.append(filter_responsible)
    if filter_status:
        query += " AND 订单状态 = ?"
        params.append(filter_status)
    if keyword:
        query += " AND (客户名称 LIKE ? OR 信保单号 LIKE ?)"
        params.extend([f"%{keyword}%"] * 2)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# 主界面切换
page = st.sidebar.selectbox("选择功能", ["登记订单", "查看与跟进订单", "快递轨迹查询"])

if page == "登记订单":
    st.title("📝 登记订单")
    with st.form("order_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            日期 = st.date_input("日期", value=datetime.today())
            信保单号 = st.text_input("信保单号")
            负责人 = st.selectbox("负责人", ["Tina", "Archie", "Sarah"])
            客户名称 = st.text_input("客户名称")
        with col2:
            国家 = st.text_input("国家")
            产品名称 = st.selectbox("产品名称", [" 亚克力挂件", "CD挂件", " 冰箱贴", " 胸牌", " 摆件", " 手机支架", " 登山扭"])
            件数 = st.number_input("件数", step=1)
            汇率 = st.number_input("汇率", step=0.01, format="%.2f")
        with col3:
            产品总价_美元 = st.number_input(" 产品总价（$）", step=0.01)
            计重 = st.number_input(" 计重", step=0.01)
            运费_美元 = st.number_input(" 运费（$）", step=0.01)
            物流 = st.selectbox("物流", ["义乌浩远", "杭州洲驰"])

        产品总价_元 = round(产品总价_美元 * 汇率, 2)
        运费_元 = round(运费_美元 * 汇率, 2)
        物流费 = st.number_input("物流费", step=0.01)
        备注 = st.text_area("备注")

        submitted = st.form_submit_button("提交订单")
        if submitted:
            insert_order((str(日期), 信保单号, 负责人, 客户名称, 国家, 产品名称, 件数, 汇率,
                          产品总价_美元, 产品总价_元, 计重, 运费_美元, 运费_元, 物流, 物流费, 备注))
            st.success(" 订单登记成功！")

elif page == "查看与跟进订单":
    st.title("📋 查看与跟进订单")
    st.markdown("### 筛选条件")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_responsible = st.selectbox("按负责人筛选", ["全部", "Tina", "Archie", "Sarah"])
        if selected_responsible == " 全部":
            selected_responsible = None
    with col2:
        selected_status = st.selectbox(" 按订单状态筛选", ["全部", "已排图", "已生产", "已发货", "已完成"])
        if selected_status == "全部":
            selected_status = None
    with col3:
        keyword = st.text_input("搜索客户名称或信保单号")

    df = get_orders(selected_responsible, selected_status, keyword)
    st.dataframe(df, use_container_width=True, height=600)

    for idx, row in df.iterrows():
        with st.expander(f"订单号: {row['信保单号']} - 客户: {row['客户名称']}"):
            new_status = st.selectbox(
                " 更新订单状态",
                ["已排图", "已生产", "已发货", "已完成"],
                index=["已排图", "已生产", "已发货", "已完成"].index(row["订单状态"]) if row["订单状态"] in ["已排图", "已生产", "已发货", "已完成"] else 0,
                key=f"status_{row['id']}"
            )
            followup_note = st.text_area("跟进备注", value=row.get("跟进备注", ""), key=f"note_{row['id']}")
            if st.button("保存修改", key=f"save_{row['id']}"):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("UPDATE orders SET 订单状态=?, 跟进备注=? WHERE id=?", (new_status, followup_note, row['id']))
                conn.commit()
                conn.close()
                st.success(" 状态和备注已更新")
                st.rerun()

elif page == "快递轨迹查询":
    import requests
    import json

    st.title("📦 快递轨迹查询工具")
    st.markdown("请输入需要查询的运单号：")

    tracking_number = st.text_input("运单号", placeholder="例如：YT1234567890")

    if tracking_number:
        with st.spinner("查询中，请稍候..."):
            url = "http://order.hy-express.com/webservice/PublicService.asmx/ServiceInterfaceUTF8"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            payload = {
                "appToken": "3f7e28f91fe9012a8cf511673228d5b6",
                "appKey": "a68b54a8852c481d00ad92625da6a6e8a68b54a8852c481d00ad92625da6a6e8",
                "serviceMethod": "gettrack",
                "paramsJson": json.dumps({
                    "tracking_number": tracking_number,
                })
            }

            try:
                response = requests.post(url, headers=headers, data=payload)
                response.raise_for_status()
                get_data = json.loads(response.text).get("data", [])
            except Exception as e:
                st.error(f"查询失败：{e}")
                st.stop()

            if not get_data:
                st.warning("未找到对应的运单信息，请确认运单号是否正确。")
            else:
                st.success("查询成功，以下是物流轨迹：")
                for data in get_data:
                    details = data.get("details", [])
                    for detail in details:
                        st.markdown(f"""
                        - **时间：** {detail.get("track_occur_date", "")}  
                          **地点：** {detail.get("track_location", "")}  
                          **状态：** {detail.get("track_description", "")}
                        """)

    st.markdown("---")
    st.caption("浩远物流")
