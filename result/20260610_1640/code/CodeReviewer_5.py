else:
        # 初次加载自动获取数据
        with st.spinner("首次加载，请稍候..."):
            initial_data = fetch_bitcoin_data()
            if initial_data:
                st.session_state.bitcoin_data = initial_data
                st.rerun()
            else:
                st.error("🚨 无法获取初始数据，请检查网络连接或稍后重试。")
