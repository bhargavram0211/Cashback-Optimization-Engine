"""
Cashback Optimization Engine - Streamlit Frontend
Sprint 2: Authentication, Onboarding & Plaid Link Integration

Major updates:
- Password-based authentication
- Session management with st.session_state
- Guided onboarding flow
- Plaid Link integration
- Landing page for signup/login
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from typing import Optional, Dict, Any
import streamlit.components.v1 as components

# Backend Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="Cashback Optimizer",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# AUTHENTICATION & SESSION MANAGEMENT
# ============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "onboarding_completed" not in st.session_state:
        st.session_state.onboarding_completed = False


def signup(email: str, password: str, name: Optional[str] = None) -> tuple[bool, str]:
    """
    Sign up a new user.
    
    Returns:
        (success, message)
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/signup",
            json={"email": email, "password": password, "name": name}
        )
        
        if response.status_code == 201:
            data = response.json()
            # Store session
            st.session_state.authenticated = True
            st.session_state.user_id = data["user_id"]
            st.session_state.session_token = data["session_token"]
            st.session_state.user_email = data["email"]
            st.session_state.user_name = data.get("name")
            st.session_state.onboarding_completed = data["onboarding_completed"]
            return True, data["message"]
        else:
            error = response.json().get("detail", "Signup failed")
            return False, error
            
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Login an existing user.
    
    Returns:
        (success, message)
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Store session
            st.session_state.authenticated = True
            st.session_state.user_id = data["user_id"]
            st.session_state.session_token = data["session_token"]
            st.session_state.user_email = data["email"]
            st.session_state.user_name = data.get("name")
            st.session_state.onboarding_completed = data["onboarding_completed"]
            return True, data["message"]
        else:
            error = response.json().get("detail", "Login failed")
            return False, error
            
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def logout():
    """Logout current user."""
    try:
        if st.session_state.session_token:
            requests.post(
                f"{BACKEND_URL}/auth/logout",
                headers={"Authorization": f"Bearer {st.session_state.session_token}"}
            )
    except:
        pass  # Logout locally even if backend call fails
    
    # Clear session
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.session_token = None
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.onboarding_completed = False


def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers for API requests."""
    if st.session_state.session_token:
        return {"Authorization": f"Bearer {st.session_state.session_token}"}
    return {}


def mark_onboarding_complete():
    """Mark user's onboarding as completed."""
    try:
        response = requests.patch(
            f"{BACKEND_URL}/auth/onboarding-complete",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            st.session_state.onboarding_completed = True
            return True
    except:
        pass
    return False


# ============================================================================
# PLAID LINK INTEGRATION
# ============================================================================

def create_link_token() -> Optional[str]:
    """
    Create a Plaid Link token for the current user.
    
    Returns:
        link_token or None if error
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/plaid/create-link-token",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()["link_token"]
    except:
        pass
    return None


def connect_sandbox() -> Optional[Dict]:
    """
    Connect to Plaid Sandbox for testing.
    
    Returns:
        Connection result with transactions synced info
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/plaid/connect-sandbox",
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def exchange_public_token(public_token: str, institution_id: str, institution_name: str) -> Optional[Dict]:
    """
    Exchange Plaid public token for access token and sync transactions.
    
    Returns:
        Exchange result or None if error
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/plaid/exchange-token",
            json={
                "public_token": public_token,
                "institution_id": institution_id,
                "institution_name": institution_name
            },
            headers=get_auth_headers()
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


# ============================================================================
# DATA FETCHING (From Sprint 1)
# ============================================================================

def fetch_savings_report(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the consolidated savings report from the backend API."""
    try:
        response = requests.get(f"{BACKEND_URL}/reports/savings/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from backend: {str(e)}")
        return None


def fetch_card_products() -> Optional[list]:
    """Fetch all card products from the master library."""
    try:
        response = requests.get(f"{BACKEND_URL}/cards/card-products")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch card products from backend: {str(e)}")
        return None


def fetch_unidentified_cards(user_id: str) -> Optional[list]:
    """Fetch user's unidentified cards."""
    try:
        response = requests.get(f"{BACKEND_URL}/cards/user-cards/unidentified?user_id={user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch unidentified cards: {str(e)}")
        return None


def identify_card(user_card_id: str, card_product_id: str) -> bool:
    """Identify a user's card as a specific card product."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/cards/user-cards/{user_card_id}/identify",
            params={"card_product_id": card_product_id}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to identify card: {str(e)}")
        return False


# ============================================================================
# PAGES: LANDING & AUTH
# ============================================================================

def landing_page():
    """Landing page with signup and login."""
    st.title("💳 Cashback Optimization Engine")
    
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2>Maximize Your Credit Card Rewards</h2>
        <p style="font-size: 18px; color: #666;">
            Discover which card to use for every purchase and never leave money on the table again.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Feature highlights
        st.markdown("### How It Works")
        st.markdown("""
        1. 🔗 **Connect Your Banks** - Securely link your accounts via Plaid
        2. 🃏 **Identify Your Cards** - Tell us which cards you own
        3. 📊 **See Your Savings** - Discover opportunities to earn more cashback
        4. 🎯 **Optimize Spending** - Get recommendations for every purchase
        """)
        
        st.markdown("---")
        
        # Tab for signup vs login
        tab_signup, tab_login = st.tabs(["Sign Up", "Login"])
        
        with tab_signup:
            st.subheader("Create Your Account")
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                name = st.text_input("Name (Optional)", key="signup_name")
                password = st.text_input("Password (min 8 characters)", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
                
                submitted = st.form_submit_button("Sign Up", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.error("Email and password are required")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters")
                    elif password != confirm_password:
                        st.error("Passwords don't match")
                    else:
                        with st.spinner("Creating your account..."):
                            success, message = signup(email, password, name if name else None)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        
        with tab_login:
            st.subheader("Welcome Back")
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                
                submitted = st.form_submit_button("Login", use_container_width=True)
                
                if submitted:
                    if not email or not password:
                        st.error("Email and password are required")
                    else:
                        with st.spinner("Logging in..."):
                            success, message = login(email, password)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; color: #999; padding: 40px 20px; margin-top: 40px; border-top: 1px solid #eee;">
        <p>🔒 Your data is secure. We use Plaid for bank connections and never store your login credentials.</p>
        <p style="font-size: 12px;">Cashback Optimization Engine - Built for smart spenders</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# PAGES: ONBOARDING
# ============================================================================

def onboarding_page():
    """Guided onboarding flow for new users."""
    st.title("🚀 Welcome to Cashback Optimizer!")
    
    # Progress tracking
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1
    
    # Track if link token was created (for Step 2)
    if "link_token_created" not in st.session_state:
        st.session_state.link_token_created = False
    
    # Progress bar
    progress = (st.session_state.onboarding_step - 1) / 3
    st.progress(progress)
    st.markdown(f"**Step {st.session_state.onboarding_step} of 3**")
    st.markdown("---")
    
    # Step 1: Welcome
    if st.session_state.onboarding_step == 1:
        st.subheader("Step 1: How It Works")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 Real-Time Analysis
            We analyze every transaction to show you:
            - How much cashback you earned
            - How much you could have earned
            - Which card would have been better
            """)
            
            st.markdown("""
            ### 🎯 Smart Recommendations
            Get personalized suggestions for:
            - Optimal card usage
            - New cards to apply for
            - Categories where you're losing money
            """)
        
        with col2:
            st.markdown("""
            ### 🔒 Secure & Private
            - Bank connections via Plaid (bank-level security)
            - We never store your login credentials
            - Your data is encrypted and private
            """)
            
            st.markdown("""
            ### 💡 Easy to Use
            - Connect in under 2 minutes
            - Automatic transaction syncing
            - Beautiful, intuitive dashboard
            """)
        
        st.markdown("---")
        
        if st.button("Get Started →", use_container_width=True, type="primary"):
            st.session_state.onboarding_step = 2
            st.rerun()
    
    # Step 2: Connect Bank
    elif st.session_state.onboarding_step == 2:
        st.subheader("Step 2: Connect Your Bank")
        
        st.markdown("""
        We use **Plaid** to securely connect to your bank. Plaid is trusted by:
        - Venmo, Cash App, and thousands of fintech apps
        - Used by over 12,000+ financial institutions
        - Bank-level 256-bit encryption
        """)
        
        st.info("💡 **Tip:** You can connect multiple banks if you have credit cards from different institutions.")
        
        # Only create link token once
        if not st.session_state.link_token_created:
            # Plaid Link Button
            if st.button("🔗 Connect Bank Account", use_container_width=True, type="primary"):
                with st.spinner("Opening Plaid Link..."):
                    link_token = create_link_token()
                    
                    if link_token:
                        st.session_state.link_token_created = True
                        st.session_state.link_token = link_token
                        st.rerun()
                    else:
                        st.error("Failed to create Plaid Link token. Please try again.")
        else:
            # Show the link token info and simulation button
            st.success("✅ Plaid Link token created!")
            
            st.markdown("---")
            st.markdown("### 🏦 Use Plaid's Test Credentials")
            st.markdown("""
            For testing, use Plaid Sandbox credentials:
            - **Username:** `user_good`
            - **Password:** `pass_good`
            - **Institution:** Any (Chase, Wells Fargo, etc.)
            """)
            
            st.markdown(f"**Link Token:** `{st.session_state.link_token[:20]}...`")
            
            # Manual token exchange for MVP
            st.markdown("---")
            st.markdown("### ⚠️ MVP: Connect to Sandbox")
            st.markdown("""
            Click below to connect to Plaid Sandbox and sync real test transactions.
            """)
            
            if st.button("✅ Connect to Plaid Sandbox", type="primary"):
                with st.spinner("Connecting to Plaid Sandbox and syncing transactions..."):
                    result = connect_sandbox()
                    
                    if result:
                        st.success(f"✅ {result['message']}")
                        st.info(f"📊 **{result['transactions_synced']}** transactions synced")
                        st.info(f"💳 **{result['cards_found']}** credit cards found")
                        
                        # Store result in session
                        st.session_state.sandbox_connected = True
                        st.session_state.cards_found = result['cards_found']
                        
                        # Move to next step
                        st.session_state.onboarding_step = 3
                        st.session_state.link_token_created = False  # Reset for next time
                        st.rerun()
                    else:
                        st.error("❌ Failed to connect to Plaid Sandbox. Please check your Plaid credentials in .env")
        
        st.markdown("---")
        if st.button("← Back"):
            st.session_state.onboarding_step = 1
            st.session_state.link_token_created = False  # Reset
            st.rerun()
    
    # Step 3: Identify Cards
    elif st.session_state.onboarding_step == 3:
        st.subheader("Step 3: Identify Your Cards")
        
        st.markdown("""
        Great! We found your credit card accounts. 
        Please tell us which card product each account represents.
        """)
        
        # Check for unidentified cards
        unidentified_cards = fetch_unidentified_cards(st.session_state.user_id)
        
        if unidentified_cards and len(unidentified_cards) > 0:
            st.info(f"📋 Found {len(unidentified_cards)} card(s) to identify")
            
            # Show identify cards flow (from Sprint 1)
            card_products = fetch_card_products()
            
            if card_products:
                for card in unidentified_cards:
                    with st.container():
                        st.markdown(f"**🃏 {card.get('official_name', 'Unknown Card')}**")
                        st.caption(f"Account ending in {card.get('mask', 'XXXX')}")
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            selected_product = st.selectbox(
                                "Select card product:",
                                options=[(cp["id"], f"{cp['provider']} {cp['card_name']}") for cp in card_products],
                                format_func=lambda x: x[1],
                                key=f"select_{card['id']}"
                            )
                        
                        with col2:
                            if st.button("Identify", key=f"btn_{card['id']}"):
                                if identify_card(card['id'], selected_product[0]):
                                    st.success("✅ Identified!")
                                    st.rerun()
                        
                        st.markdown("---")
        else:
            st.success("✅ All cards identified!")
            
            st.markdown("---")
            st.markdown("### 🎉 You're All Set!")
            st.markdown("""
            Your account is configured and ready to go. You can now:
            - View your cashback optimization dashboard
            - See where you're losing money
            - Discover better card options
            """)
            
            if st.button("Go to Dashboard →", use_container_width=True, type="primary"):
                mark_onboarding_complete()
                st.rerun()
        
        st.markdown("---")
        if st.button("← Back"):
            st.session_state.onboarding_step = 2
            st.rerun()


# ============================================================================
# PAGES: DASHBOARD (From Sprint 1 - preserved)
# ============================================================================

def dashboard_page(user_id: str):
    """Main dashboard showing savings insights and recommendations."""
    st.title("💳 Cashback Optimization Dashboard")
    st.markdown("**Maximize your credit card rewards by using the right card for every purchase.**")
    st.markdown("---")
    
    # Fetch data from backend
    with st.spinner("Loading your savings insights..."):
        report = fetch_savings_report(user_id)
    
    if not report:
        # Empty state
        st.info("👋 Welcome! Let's get you started.")
        st.markdown("""
        ### No transactions found yet
        
        To see your cashback optimization insights:
        1. Make sure you've connected your bank accounts
        2. Identified your credit cards
        3. Have some transactions synced
        
        If you just connected your bank, it may take a moment for transactions to sync.
        """)
        
        if st.button("🔄 Refresh", type="primary"):
            st.rerun()
        return
    
    summary = report.get("summary", {})
    category_breakdown = report.get("category_breakdown", [])
    top_recommendation = report.get("top_recommendation")
    
    # Top-Level Metrics
    st.subheader("📊 Your Spending Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Total Spent",
            value=f"${summary.get('total_spent', 0):,.2f}",
            help="Total amount spent across all transactions"
        )
    
    with col2:
        st.metric(
            label="✨ Actual Rewards",
            value=f"${summary.get('total_earned', 0):,.2f}",
            delta=f"{(summary.get('total_earned', 0) / summary.get('total_spent', 1) * 100):.2f}% cashback",
            help="Total cashback earned with current card usage"
        )
    
    with col3:
        lost_savings = summary.get('total_lost_savings', 0)
        st.metric(
            label="💸 Lost Savings",
            value=f"${lost_savings:,.2f}",
            delta=f"-{(lost_savings / summary.get('total_spent', 1) * 100):.2f}%",
            delta_color="inverse",
            help="Opportunity cost from not using optimal cards"
        )
    
    st.markdown("---")
    
    # Category Breakdown
    st.subheader("📈 Lost Savings by Category")
    
    if category_breakdown:
        df_categories = pd.DataFrame(category_breakdown)
        df_categories = df_categories.sort_values('lost_savings', ascending=False)
        
        col_chart, col_insights = st.columns([2, 1])
        
        with col_chart:
            fig = px.bar(
                df_categories,
                x='category',
                y='lost_savings',
                title="Opportunity Cost by Spending Category",
                labels={'lost_savings': 'Lost Savings ($)', 'category': 'Category'},
                color='lost_savings',
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_insights:
            st.markdown("#### 💡 Key Insights")
            top_cat = df_categories.iloc[0]
            st.markdown(f"""
            **Biggest Opportunity:** {top_cat['category']}
            - Lost: ${top_cat['lost_savings']:.2f}
            - Spent: ${top_cat['total_spent']:.2f}
            - Could earn: ${top_cat['potential_cashback']:.2f}
            """)
            
            if len(df_categories) > 1:
                second_cat = df_categories.iloc[1]
                st.markdown(f"""
                **Second:** {second_cat['category']}
                - Lost: ${second_cat['lost_savings']:.2f}
                """)
    
    st.markdown("---")
    
    # Top Recommendation
    if top_recommendation:
        st.subheader("🏆 Top Card Recommendation")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            ### {top_recommendation['provider']} {top_recommendation['card_name']}
            
            This card was the optimal choice for **{top_recommendation['times_recommended']}** of your transactions.
            
            **Potential Savings:** ${top_recommendation['total_potential_savings']:.2f}  
            **Avg per Transaction:** ${top_recommendation['avg_savings_per_transaction']:.2f}
            """)
        
        with col2:
            st.metric(
                "Times Recommended",
                top_recommendation['times_recommended'],
                help="Number of transactions where this card was optimal"
            )


# ============================================================================
# PAGES: CARD DISCOVERY & IDENTIFY (From Sprint 1 - preserved)
# ============================================================================

def get_category_icon(bucket: str) -> str:
    """Get emoji icon for reward bucket."""
    icons = {
        "DINING": "🍽️",
        "GROCERY": "🛒",
        "TRAVEL": "✈️",
        "GAS": "⛽",
        "DRUGSTORE": "💊",
        "ONLINE_SHOPPING": "🛍️",
        "ENTERTAINMENT": "🎬",
        "GENERAL": "💳"
    }
    return icons.get(bucket, "💳")


def get_best_category_for_card(card: Dict) -> tuple[str, float]:
    """Get the best reward category for a card."""
    if not card.get("reward_rules"):
        return "All Purchases", card.get("base_reward_rate", 0)
    
    best_rule = max(card["reward_rules"], key=lambda x: x["multiplier"])
    return best_rule["bucket"], best_rule["multiplier"]


def card_discovery_page():
    """Card discovery page with search and filters."""
    st.title("🔍 Card Discovery")
    st.markdown("**Explore credit cards and find the best ones for your spending.**")
    st.markdown("---")
    
    # Fetch cards
    with st.spinner("Loading card library..."):
        cards = fetch_card_products()
    
    if not cards:
        st.error("Unable to load cards from backend")
        return
    
    st.success(f"✅ Found {len(cards)} credit cards")
    
    # Search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search by provider or card name", "")
    
    with col2:
        category_filter = st.multiselect(
            "Filter by category",
            options=["DINING", "GROCERY", "TRAVEL", "GAS", "DRUGSTORE", "ONLINE_SHOPPING", "ENTERTAINMENT"],
            format_func=lambda x: f"{get_category_icon(x)} {x.title()}"
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["provider", "base_rate", "num_categories"],
            format_func=lambda x: {
                "provider": "Provider (A-Z)",
                "base_rate": "Highest Base Rate",
                "num_categories": "Most Categories"
            }[x]
        )
    
    # Filter cards
    filtered_cards = cards
    
    if search_query:
        filtered_cards = [
            c for c in filtered_cards
            if search_query.lower() in c["provider"].lower() 
            or search_query.lower() in c["card_name"].lower()
        ]
    
    if category_filter:
        filtered_cards = [
            c for c in filtered_cards
            if any(rule["bucket"] in category_filter for rule in c.get("reward_rules", []))
        ]
    
    # Sort cards
    if sort_by == "provider":
        filtered_cards.sort(key=lambda x: (x["provider"], x["card_name"]))
    elif sort_by == "base_rate":
        filtered_cards.sort(key=lambda x: x.get("base_reward_rate", 0), reverse=True)
    elif sort_by == "num_categories":
        filtered_cards.sort(key=lambda x: len(x.get("reward_rules", [])), reverse=True)
    
    st.markdown(f"**Showing {len(filtered_cards)} cards**")
    st.markdown("---")
    
    # Display cards in 3-column grid
    for i in range(0, len(filtered_cards), 3):
        cols = st.columns(3)
        
        for j, col in enumerate(cols):
            if i + j < len(filtered_cards):
                card = filtered_cards[i + j]
                best_category, best_rate = get_best_category_for_card(card)
                
                with col:
                    with st.container():
                        # Card header
                        st.markdown(f"### {card['provider']}")
                        st.markdown(f"**{card['card_name']}**")
                        
                        # Best category badge
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; padding: 8px; border-radius: 8px; text-align: center; margin: 10px 0;">
                            <strong>Best: {best_rate}% {get_category_icon(best_category)} {best_category.title()}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Base rate
                        st.caption(f"Base: {card.get('base_reward_rate', 0)}% on all purchases")
                        
                        # Reward rules
                        if card.get("reward_rules"):
                            with st.expander("View Reward Details"):
                                for rule in sorted(card["reward_rules"], key=lambda x: x["multiplier"], reverse=True):
                                    st.markdown(f"- {get_category_icon(rule['bucket'])} **{rule['multiplier']}%** {rule['bucket'].title()}")
                        
                        # Benefits link
                        if card.get("benefits_url"):
                            st.markdown(f"[View Benefits ↗]({card['benefits_url']})")
                        
                        st.markdown("---")


def identify_cards_page(user_id: str):
    """Card identification page."""
    st.title("🔍 Identify Your Cards")
    st.markdown("**Link your bank accounts to specific card products so we can calculate accurate rewards.**")
    st.markdown("---")
    
    # Fetch unidentified cards
    with st.spinner("Loading your cards..."):
        unidentified_cards = fetch_unidentified_cards(user_id)
        card_products = fetch_card_products()
    
    if not card_products:
        st.error("❌ Unable to load card products from backend")
        return
    
    if not unidentified_cards:
        # No unidentified cards
        st.success("✅ **All your cards are identified!**")
        st.markdown("""
        All your Plaid-synced credit cards have been identified. You can now:
        - View your **Dashboard** to see savings insights
        - Explore the **Card Discovery** page to find new cards
        """)
        
        st.info("💡 **Tip:** If you connect a new bank account, come back here to identify those cards.")
        return
    
    # Display unidentified cards
    st.subheader(f"📋 Unidentified Cards ({len(unidentified_cards)})")
    st.markdown("We found these credit cards in your connected bank accounts. Please tell us which card product each one is:")
    
    st.markdown("---")
    
    # Create a form for each unidentified card
    for card in unidentified_cards:
        with st.container():
            st.markdown(f"### 🃏 {card.get('official_name', 'Unknown Card')}")
            st.caption(f"Account ending in **{card.get('mask', 'XXXX')}**")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_product = st.selectbox(
                    "Which card is this?",
                    options=[(cp["id"], f"{cp['provider']} {cp['card_name']}") for cp in card_products],
                    format_func=lambda x: x[1],
                    key=f"select_{card['id']}"
                )
            
            with col2:
                if st.button("✅ Identify", key=f"btn_{card['id']}", use_container_width=True):
                    if identify_card(card['id'], selected_product[0]):
                        st.success("Identified!")
                        st.rerun()
            
            st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>Your card information is securely linked through Plaid</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION LOGIC
# ============================================================================

def main():
    """Main application entry point."""
    init_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        landing_page()
        return
    
    # Check onboarding
    if not st.session_state.onboarding_completed:
        onboarding_page()
        return
    
    # Main application (authenticated + onboarded)
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    
    # User info
    st.sidebar.markdown(f"**👤 {st.session_state.user_name or st.session_state.user_email}**")
    st.sidebar.caption(f"{st.session_state.user_email}")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Page selection
    page = st.sidebar.radio(
        "Choose a page:",
        ["My Dashboard", "Identify My Cards", "Card Discovery"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # About section
    if page == "My Dashboard":
        st.sidebar.markdown("""
        ### 💡 About
        This dashboard shows your credit card cashback optimization insights:
        - **Total Spent**: Your transaction volume
        - **Actual Rewards**: Cashback you earned
        - **Lost Savings**: Opportunity cost from suboptimal card usage
        """)
    elif page == "Identify My Cards":
        st.sidebar.markdown("""
        ### 💡 About Card Identification
        Link your Plaid-synced bank accounts to specific card products:
        - We detect your credit cards from Plaid
        - You tell us which product each card is
        - We calculate accurate rewards based on real usage
        """)
    
    # Route to appropriate page
    if page == "My Dashboard":
        dashboard_page(st.session_state.user_id)
    elif page == "Identify My Cards":
        identify_cards_page(st.session_state.user_id)
    else:
        card_discovery_page()


if __name__ == "__main__":
    main()
