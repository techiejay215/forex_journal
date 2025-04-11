import streamlit as st
import pandas as pd
import plotly.express as px
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set page title and icon
st.set_page_config(page_title="Forex Trading Journal", page_icon="📈")

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Sample DataFrame for trade logs
df = pd.read_csv("trade_journal.csv") if os.path.exists("trade_journal.csv") else pd.DataFrame(
    columns=["Pair", "Entry", "SL", "TP", "Result", "P/L (pips)", "R:R", "Date"]
)

# Function to send email alerts
def send_email(subject, body, to_email):
    sender_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not password:
        st.error("Email credentials are not set in environment variables.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        st.success("Email sent successfully!")
    except Exception as e:
        st.error(f"Error sending email: {e}")

# Sidebar Navigation
st.sidebar.header("Navigation")
option = st.sidebar.radio(
    "Choose an option",
    ["Login", "Log Trade", "View Performance", "Settings"]
)

# ------------------ LOGIN ------------------
if option == "Login":
    st.title("🔐 Login to Your Forex Journal")

    with st.form(key="login_form"):
        username = st.text_input("Username (Email)", placeholder="Enter your email")
        password = st.text_input("Password", type='password', placeholder="Enter your password")
        submit_button = st.form_submit_button(label="Login")

        if submit_button:
            real_username = st.secrets["credentials"]["username"]
            real_password = st.secrets["credentials"]["password"]

            if username == real_username and password == real_password:
                st.session_state["logged_in"] = True
                st.success("✅ Logged in successfully!")
            else:
                st.error("❌ Invalid login credentials!")

# ------------------ MAIN APP ------------------
if st.session_state.get("logged_in"):
    st.title("📒 Forex Trade Journal")

    # Main Dashboard - Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Log Trade", "📈 View Performance", "⚙️ Settings"])

    # Log Trade Tab
    with tab1:
        st.subheader("📌 Log Your Trade")

        with st.form(key="trade_form"):
            pair = st.text_input("Currency Pair (e.g., EURUSD)")
            entry = st.number_input("Entry Price", min_value=0.0, format="%.5f")
            sl = st.number_input("Stop Loss", min_value=0.0, format="%.5f")
            tp = st.number_input("Take Profit", min_value=0.0, format="%.5f")
            result = st.selectbox("Trade Result", ["Win", "Loss", "Breakeven"])
            date = st.date_input("Trade Date")

            submit_button = st.form_submit_button(label="Log Trade")

            if submit_button:
                # Calculate P/L and R:R safely
                try:
                    if result == "Win":
                        pl = tp - entry
                        rr = pl / (tp - entry) if (tp - entry) != 0 else 0
                    elif result == "Loss":
                        pl = entry - sl
                        rr = pl / (entry - sl) if (entry - sl) != 0 else 0
                    else:  # Breakeven
                        pl = 0
                        rr = 0
                except ZeroDivisionError:
                    pl = 0
                    rr = 0

                new_trade = pd.DataFrame([[pair, entry, sl, tp, result, pl, rr, date]], columns=df.columns)
                df = pd.concat([df, new_trade], ignore_index=True)
                df.to_csv("trade_journal.csv", index=False)
                st.success(f"✅ Trade logged successfully for {pair} on {date}!")

    # View Performance Tab
    with tab2:
        st.subheader("📊 Trade Performance")

        if not df.empty:
            st.dataframe(df)

            win_rate = (df["Result"] == "Win").mean() * 100
            avg_rr = df["R:R"].mean()

            st.subheader("📈 Summary")
            st.write(f"**Win Rate**: {win_rate:.2f}%")
            st.write(f"**Average R:R**: {avg_rr:.2f}")

            fig = px.pie(names=["Wins", "Others"], values=[win_rate, 100 - win_rate], title="Win/Loss Distribution")
            st.plotly_chart(fig)

            st.download_button(
                label="📥 Download Trade Data",
                data=df.to_csv(index=False),
                file_name="trade_journal.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades logged yet!")

    # Settings Tab
    with tab3:
        st.subheader("⚙️ Settings")
        st.write("This section is under construction. Soon, you will be able to update your login or notification preferences.")

else:
    if option != "Login":
        st.warning("🔒 Please log in to access the trade journal.")
