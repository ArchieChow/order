import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB = "orders.db"

负责人列表 = ["Tina", "Archie", "Sarah"]
产品列表 = ["亚克力挂件", "CD挂件", "冰箱贴", "胸牌", "摆件", "手机支架", "登山扣"]
物流选项 = ["义乌浩远", "杭州洲驰"]
状态选项 = ["已排图", "已生产", "已发货", "已完成"]

def create_table():
    conn = sqlite3.connect(DB)
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
            产品总价美元 REAL,
            产品总价元 REAL,
            计重 REAL,
            运费美元 REAL,
            运费元 REAL,
            物流 TEXT,
            物流费 REAL,
            备注 TEXT,
            订单状态 TEXT DEFAULT '排图',
            跟进备注 TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_order(data):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (
            日期, 信保单号, 负责人, 客户名称, 国家, 产品名称, 件数,
            汇率, 产品总价美元, 产品总价元, 计重, 运费美元, 运费元,
            物流, 物流费, 备注, 订单状态, 跟进备注
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def load_orders(负责人=None, 状态=None, keyword=None):
    conn = sqlite3.connect(DB)
    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if 负责人:
        query += " AND 负责人=?"
        params.append(负责人)
    if 状态:
        query += " AND 订单状态=?"
        params.append(状态)
    if keyword:
        query += " AND (客户名称 LIKE ? OR 信保单号 LIKE ?)"
        keyword_param = f"%{keyword}%"
        params.extend([keyword_param, keyword_param])

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def main():
    st.set_page_config(layout="wide")
    st.title("订单登记与跟进系统")

    tabs = st.tabs(["登记订单", "查看与跟进订单"])

    with tabs[0]:
        st.subheader("登记新订单")
        with st.form("entry_form"):
            日期 = st.date_input("日期", value=datetime.today())
            信保单号 = st.text_input("信保单号")
            负责人 = st.selectbox("负责人", 负责人列表)
            客户名称 = st.text_input("客户名称")
            国家 = st.text_input("国家")
            产品名称 = st.selectbox("产品名称", 产品列表)
            件数 = st.number_input("件数", step=1, min_value=0)
            汇率 = st.number_input("汇率", step=0.01)
            产品总价美元 = st.number_input("产品总价（$）", step=0.01)
            产品总价元 = 产品总价美元 * 汇率
            计重 = st.number_input("计重", step=0.01)
            运费美元 = st.number_input("运费（$）", step=0.01)
            运费元 = 运费美元 * 汇率
            物流 = st.selectbox("物流", 物流选项)
            物流费 = st.number_input("物流费", step=0.01)
            备注 = st.text_area("备注")
            跟进备注 = ""
            提交 = st.form_submit_button("提交")

            if 提交:
                data = (
                    str(日期), 信保单号, 负责人, 客户名称, 国家, 产品名称, 件数,
                    汇率, 产品总价美元, 产品总价元, 计重, 运费美元, 运费元,
                    物流, 物流费, 备注, "排图", 跟进备注
                )
                insert_order(data)
                st.success("订单已登记")

    with tabs[1]:
        st.subheader("查看与跟进订单")
        col1, col2, col3 = st.columns(3)
        with col1:
            负责人过滤 = st.selectbox("筛选负责人", ["全部"] + 负责人列表)
            if 负责人过滤 == "全部":
                负责人过滤 = None
        with col2:
            状态过滤 = st.selectbox("筛选订单状态", ["全部"] + 状态选项)
            if 状态过滤 == "全部":
                状态过滤 = None
        with col3:
            keyword = st.text_input("搜索客户名称或信保单号")

        df = load_orders(负责人过滤, 状态过滤, keyword)

        if df.empty:
            st.info("没有符合条件的订单记录")
        else:
            for idx, row in df.iterrows():
                with st.expander(f"订单ID {row['id']} - {row['客户名称']} [{row['订单状态']}]", expanded=False):
                    st.write("客户名称:", row['客户名称'])
                    st.write("产品:", row['产品名称'])
                    st.write("国家:", row['国家'])
                    st.write("备注:", row['备注'])
                    new_status = st.selectbox(
                        "更新订单状态",
                        状态选项,
                        index=状态选项.index(row['订单状态']) if row['订单状态'] in 状态选项 else 0,
                        key=f"status_{row['id']}"
                    )
                    new_note = st.text_area("跟进备注", value=row['跟进备注'] or "", key=f"note_{row['id']}")
                    if st.button("保存", key=f"save_{row['id']}"):
                        conn = sqlite3.connect(DB)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE orders SET 订单状态=?, 跟进备注=? WHERE id=?", (new_status, new_note, row['id']))
                        conn.commit()
                        conn.close()
                        st.success("更新成功")
                        st.rerun()

if __name__ == "__main__":
    create_table()
    main()
