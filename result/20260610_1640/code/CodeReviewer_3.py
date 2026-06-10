# 初始化
    if "loading" not in st.session_state:
        st.session_state.loading = False

    # 按钮逻辑
    button_disabled = st.session_state.loading
    if st.button("🔄 刷新价格", type="primary", disabled=button_disabled):
        st.session_state.loading = True
        st.rerun()  # 立即 rerun 以禁用按钮并显示 spinner
    
    # 在 main 函数顶部检查是否需要加载
    if st.session_state.loading:
        with st.spinner("正在更新数据..."):
            new_data = fetch_bitcoin_data()
            if new_data:
                st.session_state.bitcoin_data = new_data
            st.session_state.loading = False
            st.rerun()
