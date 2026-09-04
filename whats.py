import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="WhatsApp Chat Analyzer", page_icon="💬", layout="wide")

st.sidebar.title("💬 WhatsApp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("Upload WhatsApp Exported Chat (.txt file)")

# Mobile App Chat Export Instructions Component
def render_export_instructions():
    st.markdown("""
    ### 📱 How to Export WhatsApp Chat from Mobile App
    
    If you're wondering how to get your chat file from WhatsApp to analyze here, follow these simple steps:
    """)

    tab_android, tab_ios = st.tabs(["🤖 Android Instructions", "🍎 iPhone (iOS) Instructions"])

    with tab_android:
        st.markdown("""
        1. Open **WhatsApp** on your Android phone.
        2. Open the specific individual or group chat you want to analyze.
        3. Tap the **Three Dots (⋮)** in the top-right corner.
        4. Select **More** ➔ **Export chat**.
        5. Choose **Without Media** *(Recommended for faster analysis & smaller file size)*.
        6. Save or send the `.txt` file to your computer or device and upload it using the sidebar on the left.
        """)

    with tab_ios:
        st.markdown("""
        1. Open **WhatsApp** on your iPhone.
        2. Open the individual or group chat you want to analyze.
        3. Tap the **Contact Name / Group Title** at the top of the screen.
        4. Scroll down to the bottom and tap **Export Chat**.
        5. Select **Without Media**.
        6. Choose **Save to Files** or share it to your PC, then upload the `.txt` file using the sidebar.
        """)

    st.info("💡 **Tip:** Exporting *Without Media* gives a standard `.txt` file containing all text messages, dates, and timestamps suitable for full analysis.")

if uploaded_file is None:
    st.title("Welcome to WhatsApp Chat Analyzer 📊")
    st.write("Upload an exported WhatsApp chat `.txt` file from the sidebar to generate insights, word clouds, timelines, activity maps, and emoji statistics.")
    st.markdown("---")
    render_export_instructions()
else:
    try:
        bytes_data = uploaded_file.getvalue()
        data = bytes_data.decode("utf-8")
        df = preprocessor.preprocess(data)
    except Exception as e:
        st.error(f"Error parsing uploaded file: {e}")
        df = None

    if df is None or df.empty:
        st.error("Could not extract any valid messages from the uploaded file. Please ensure you uploaded a valid WhatsApp export file (.txt format).")
        st.markdown("---")
        render_export_instructions()
    else:
        # fetch unique users
        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
            user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0, "Overall")

        selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

        # Show instructions inside sidebar expander for convenience
        with st.sidebar.expander("❓ How to export chat from WhatsApp"):
            render_export_instructions()

        if st.sidebar.button("Show Analysis"):

            # Stats Area
            num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
            st.title("Top Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.header("Total Messages")
                st.title(num_messages)
            with col2:
                st.header("Total Words")
                st.title(words)
            with col3:
                st.header("Media Shared")
                st.title(num_media_messages)
            with col4:
                st.header("Links Shared")
                st.title(num_links)

            # monthly timeline
            st.title("Monthly Timeline")
            timeline = helper.monthly_timeline(selected_user, df)
            if not timeline.empty:
                fig, ax = plt.subplots()
                ax.plot(timeline['time'], timeline['message'], color='green', marker='o')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            else:
                st.info("No monthly timeline data available.")

            # daily timeline
            st.title("Daily Timeline")
            daily_timeline = helper.daily_timeline(selected_user, df)
            if not daily_timeline.empty:
                fig, ax = plt.subplots()
                ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            else:
                st.info("No daily timeline data available.")

            # activity map
            st.title('Activity Map')
            col1, col2 = st.columns(2)

            with col1:
                st.header("Most busy day")
                busy_day = helper.week_activity_map(selected_user, df)
                if not busy_day.empty:
                    fig, ax = plt.subplots()
                    ax.bar(busy_day.index, busy_day.values, color='purple')
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)
                else:
                    st.info("No day activity data available.")

            with col2:
                st.header("Most busy month")
                busy_month = helper.month_activity_map(selected_user, df)
                if not busy_month.empty:
                    fig, ax = plt.subplots()
                    ax.bar(busy_month.index, busy_month.values, color='orange')
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)
                else:
                    st.info("No month activity data available.")

            st.title("Weekly Activity Map")
            user_heatmap = helper.activity_heatmap(selected_user, df)
            if not user_heatmap.empty and user_heatmap.shape[0] > 0 and user_heatmap.shape[1] > 0:
                fig, ax = plt.subplots()
                ax = sns.heatmap(user_heatmap)
                st.pyplot(fig)
            else:
                st.info("No heatmap data available.")

            # finding the busiest users in the group(Group level)
            if selected_user == 'Overall':
                st.title('Most Busy Users')
                x, new_df = helper.most_busy_users(df)
                if not x.empty:
                    fig, ax = plt.subplots()
                    col1, col2 = st.columns(2)

                    with col1:
                        ax.bar(x.index, x.values, color='red')
                        plt.xticks(rotation='vertical')
                        st.pyplot(fig)
                    with col2:
                        st.dataframe(new_df)

            # WordCloud
            st.title("Wordcloud")
            df_wc = helper.create_wordcloud(selected_user, df)
            if df_wc is not None:
                fig, ax = plt.subplots()
                ax.imshow(df_wc)
                ax.axis('off')
                st.pyplot(fig)
            else:
                st.info("No words available to generate Wordcloud.")

            # most common words
            most_common_df = helper.most_common_words(selected_user, df)
            st.title('Most common words')
            if not most_common_df.empty:
                fig, ax = plt.subplots()
                ax.barh(most_common_df['Word'], most_common_df['Count'])
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            else:
                st.info("No common words found.")

            # emoji analysis
            emoji_df = helper.emoji_helper(selected_user, df)
            st.title("Emoji Analysis")

            if not emoji_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(emoji_df)
                with col2:
                    fig, ax = plt.subplots()
                    ax.pie(emoji_df['Count'].head(), labels=emoji_df['Emoji'].head(), autopct="%0.2f")
                    st.pyplot(fig)
            else:
                st.info("No emojis found in the chat.")

        # --- Add Custom Stop Words Section ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛑 Manage Stop Words")
        st.sidebar.write("Add custom words to ignore in analysis.")
        new_stop_word = st.sidebar.text_input("New Stop Word")
        if st.sidebar.button("Add Word"):
            if new_stop_word.strip():
                try:
                    with open('stop_hinglish.txt', 'a', encoding='utf-8') as f:
                        f.write(f"\n{new_stop_word.strip().lower()}")
                    st.sidebar.success(f"Added '{new_stop_word.strip()}' successfully! Click 'Show Analysis' again.")
                except Exception as e:
                    st.sidebar.error(f"Failed to add word: {e}")
            else:
                st.sidebar.warning("Please enter a valid word.")


