"""
Cashback Optimization Engine - Streamlit Frontend
Phase 3: Interactive Dashboard for Savings Insights
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from typing import Optional, Dict, Any

# Backend Configuration
# Use Docker service name when running in container, localhost otherwise
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="Cashback Optimizer",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)


def fetch_savings_report(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the consolidated savings report from the backend API.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        Dictionary with savings report or None if error
    """
    try:
        response = requests.get(f"{BACKEND_URL}/reports/savings/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from backend: {str(e)}")
        return None


def fetch_card_products() -> Optional[list]:
    """
    Fetch all card products from the master library.
    
    Sprint 1: Updated to use /cards/card-products endpoint
    
    Returns:
        List of CardProducts or None if error
    """
    try:
        response = requests.get(f"{BACKEND_URL}/cards/card-products")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch card products from backend: {str(e)}")
        return None


def fetch_unidentified_cards(user_id: str) -> Optional[list]:
    """
    Fetch user's unidentified cards (cards synced from Plaid but not yet identified).
    
    Sprint 1: New function for card identification flow
    
    Args:
        user_id: UUID of the user
        
    Returns:
        List of unidentified UserCards or None if error
    """
    try:
        response = requests.get(f"{BACKEND_URL}/cards/user-cards/unidentified?user_id={user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch unidentified cards: {str(e)}")
        return None


def identify_card(user_card_id: str, card_product_id: str) -> bool:
    """
    Identify a user's card as a specific card product.
    
    Sprint 1: New function for card identification flow
    
    Args:
        user_card_id: UUID of the UserCard to identify
        card_product_id: UUID of the CardProduct to link to
        
    Returns:
        True if successful, False otherwise
    """
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


def fetch_transaction_opportunities(user_id: str) -> Optional[pd.DataFrame]:
    """
    Fetch transactions with optimization opportunities from the backend.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        DataFrame of transactions with lost_savings > 0
    """
    try:
        # Note: This endpoint doesn't exist yet, so we'll need to add it or work around it
        # For now, we'll use a placeholder that can be implemented later
        response = requests.get(f"{BACKEND_URL}/analytics/opportunities/{user_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except requests.exceptions.RequestException:
        # Fallback: Return None if endpoint doesn't exist yet
        return None


def dashboard_page(user_id: str):
    """
    Main dashboard showing savings insights and recommendations.
    
    Args:
        user_id: UUID of the user to display data for
    """
    # Main Content
    st.title("💳 Cashback Optimization Dashboard")
    st.markdown("**Maximize your credit card rewards by using the right card for every purchase.**")
    st.markdown("---")
    
    # Fetch data from backend
    with st.spinner("Loading your savings insights..."):
        report = fetch_savings_report(user_id)
    
    if not report:
        st.error("❌ Unable to load data. Please check:")
        st.error("1. Backend is running at http://localhost:8000")
        st.error("2. User ID is valid")
        st.error("3. User has transactions in the database")
        return
    
    summary = report.get("summary", {})
    category_breakdown = report.get("category_breakdown", [])
    top_recommendation = report.get("top_recommendation")
    
    # ========== Top-Level Metrics ==========
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
    
    # ========== Visual Insights: Category Breakdown ==========
    st.subheader("📈 Lost Savings by Category")
    
    if category_breakdown:
        # Create DataFrame for visualization
        df_categories = pd.DataFrame(category_breakdown)
        df_categories = df_categories.sort_values('lost_savings', ascending=False)
        
        # Create two columns for chart and insights
        col_chart, col_insights = st.columns([2, 1])
        
        with col_chart:
            # Use Plotly for better interactive charts
            fig = px.bar(
                df_categories,
                x='category',
                y='lost_savings',
                title='Opportunity Cost by Spending Category',
                labels={'category': 'Category', 'lost_savings': 'Lost Savings ($)'},
                color='lost_savings',
                color_continuous_scale='Reds',
                text='lost_savings'
            )
            fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
            fig.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_insights:
            st.markdown("#### 🎯 Key Insights")
            
            # Top category with most opportunity
            top_category = df_categories.iloc[0]
            st.markdown(f"""
            **Biggest Opportunity:**  
            `{top_category['category']}`
            
            - Lost: **${top_category['lost_savings']:.2f}**
            - Transactions: **{top_category['transaction_count']}**
            - Could earn: **${top_category['potential_cashback']:.2f}**
            
            💡 *Focus on optimizing this category first!*
            """)
        
        # Detailed category table
        with st.expander("📋 View Detailed Category Breakdown"):
            df_display = df_categories.copy()
            df_display['lost_savings'] = df_display['lost_savings'].apply(lambda x: f"${x:.2f}")
            df_display['actual_cashback'] = df_display['actual_cashback'].apply(lambda x: f"${x:.2f}")
            df_display['potential_cashback'] = df_display['potential_cashback'].apply(lambda x: f"${x:.2f}")
            df_display['total_spent'] = df_display['total_spent'].apply(lambda x: f"${x:.2f}")
            df_display.columns = ['Category', 'Transactions', 'Total Spent', 'Lost Savings', 
                                   'Actual Cashback', 'Potential Cashback']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No category data available.")
    
    st.markdown("---")
    
    # ========== Card MVP: Top Recommendation ==========
    st.subheader("🏆 Your Most Recommended Card")
    
    if top_recommendation:
        # Create a prominent card display
        col_card, col_stats = st.columns([1, 2])
        
        with col_card:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 30px; border-radius: 15px; color: white; text-align: center;">
                <h2 style="margin: 0; color: white;">💳</h2>
                <h3 style="margin: 10px 0; color: white;">{top_recommendation['provider']}</h3>
                <h2 style="margin: 0; color: white;">{top_recommendation['card_name']}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats:
            st.markdown("#### 📊 Impact Analysis")
            
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                st.metric(
                    "Times Recommended",
                    f"{top_recommendation['times_recommended']}",
                    help="Number of transactions where this card would be optimal"
                )
                st.metric(
                    "Total Potential Savings",
                    f"${top_recommendation['total_potential_savings']:.2f}",
                    help="Total money you could save by using this card"
                )
            
            with col_stat2:
                st.metric(
                    "Avg Savings/Transaction",
                    f"${top_recommendation['avg_savings_per_transaction']:.2f}",
                    help="Average savings per transaction with this card"
                )
                
                # Calculate percentage of transactions
                total_txns = summary.get('transaction_count', 1)
                optimal_pct = (top_recommendation['times_recommended'] / total_txns * 100)
                st.metric(
                    "Coverage",
                    f"{optimal_pct:.1f}%",
                    help="Percentage of your transactions where this card is optimal"
                )
    else:
        st.info("No card recommendations available. Please ensure you have optimized transactions.")
    
    st.markdown("---")
    
    # ========== Transaction Explorer ==========
    st.subheader("🔍 Optimization Opportunities")
    st.markdown("**Transactions where you could have earned more rewards:**")
    
    # Try to fetch transaction-level data
    opportunities_df = fetch_transaction_opportunities(user_id)
    
    if opportunities_df is not None and not opportunities_df.empty:
        # Display table of optimization opportunities
        st.dataframe(
            opportunities_df[['merchant_name', 'amount', 'internal_bucket', 
                             'actual_cashback', 'best_possible_cashback', 
                             'lost_savings', 'best_card_name']],
            use_container_width=True,
            hide_index=True
        )
    else:
        # Placeholder message when endpoint doesn't exist yet
        st.info("""
        💡 **Transaction-level explorer coming soon!**
        
        This feature will show you a detailed table of each transaction where you could have earned more rewards.
        
        For now, use the category breakdown above to identify which spending categories have the most opportunity.
        
        **To enable this feature, add a new backend endpoint:**
        `GET /analytics/opportunities/{user_id}` that returns transactions with `lost_savings > 0`
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>Built with ❤️ using FastAPI, SQLModel, Plaid, and Streamlit</p>
        <p>Cashback Optimization Engine v0.4.0</p>
    </div>
    """, unsafe_allow_html=True)


def get_category_icon(bucket: str) -> str:
    """Return an emoji icon for a spending category."""
    icons = {
        "DINING": "🍽️",
        "GROCERY": "🛒",
        "TRAVEL": "✈️",
        "GAS": "⛽",
        "STREAMING": "📺",
        "ONLINE_SHOPPING": "🛍️",
        "DRUGSTORE": "💊",
        "WHOLESALE": "🏪",
        "GENERAL": "💳"
    }
    return icons.get(bucket, "💰")


def get_best_category_for_card(card: dict) -> tuple[str, float]:
    """
    Find the best (highest multiplier) reward category for a card.
    
    Returns:
        Tuple of (category_name, multiplier)
    """
    reward_rules = card.get('reward_rules', [])
    if not reward_rules:
        return ("All Purchases", card.get('base_reward_rate', 1.0))
    
    # Find rule with highest multiplier (excluding GENERAL)
    non_general = [r for r in reward_rules if r['bucket'] != 'GENERAL']
    if not non_general:
        return ("All Purchases", card.get('base_reward_rate', 1.0))
    
    best = max(non_general, key=lambda r: r['multiplier'])
    return (best['bucket'].replace('_', ' ').title(), best['multiplier'])


def card_discovery_page():
    """
    Sprint 1 Completion: Redesigned Card Discovery Page
    
    Features:
    - Search by provider or card name
    - Filter by reward categories
    - Sort by various criteria
    - Modern 3-column grid layout
    - Card images
    - Interactive hover effects
    - Category icons
    """
    st.title("🏪 Card Discovery")
    st.markdown("**Explore our complete card library and find the perfect card for your spending.**")
    st.markdown("---")
    
    # Fetch all card products
    with st.spinner("Loading card library..."):
        cards = fetch_card_products()
    
    if not cards:
        st.error("❌ Unable to load cards from backend")
        st.info("💡 Make sure the backend is running and cards are imported via `import_cards.py`")
        return
    
    # ========== Search & Filter Controls ==========
    st.subheader("🔍 Find Your Perfect Card")
    
    col_search, col_filter, col_sort = st.columns([2, 2, 1])
    
    with col_search:
        search_query = st.text_input(
            "Search by provider or card name",
            placeholder="e.g., Chase, Amex, Gold...",
            label_visibility="collapsed"
        )
    
    with col_filter:
        # Get all unique categories from all cards
        all_categories = set()
        for card in cards:
            for rule in card.get('reward_rules', []):
                if rule['bucket'] != 'GENERAL':
                    all_categories.add(rule['bucket'])
        
        category_filter = st.multiselect(
            "Filter by reward category",
            options=sorted(all_categories),
            format_func=lambda x: f"{get_category_icon(x)} {x.replace('_', ' ').title()}",
            placeholder="All categories"
        )
    
    with col_sort:
        sort_option = st.selectbox(
            "Sort by",
            options=[
                "Provider A-Z",
                "Highest Base Rate",
                "Most Reward Categories"
            ],
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    
    # ========== Apply Filters ==========
    filtered_cards = cards
    
    # Search filter
    if search_query:
        query_lower = search_query.lower()
        filtered_cards = [
            c for c in filtered_cards
            if query_lower in c['provider'].lower() or query_lower in c['card_name'].lower()
        ]
    
    # Category filter
    if category_filter:
        filtered_cards = [
            c for c in filtered_cards
            if any(
                rule['bucket'] in category_filter
                for rule in c.get('reward_rules', [])
            )
        ]
    
    # Apply sorting
    if sort_option == "Provider A-Z":
        filtered_cards = sorted(filtered_cards, key=lambda x: (x['provider'], x['card_name']))
    elif sort_option == "Highest Base Rate":
        filtered_cards = sorted(filtered_cards, key=lambda x: x.get('base_reward_rate', 0), reverse=True)
    elif sort_option == "Most Reward Categories":
        filtered_cards = sorted(
            filtered_cards,
            key=lambda x: len([r for r in x.get('reward_rules', []) if r['bucket'] != 'GENERAL']),
            reverse=True
        )
    
    # ========== Display Results ==========
    result_count = len(filtered_cards)
    
    if result_count == 0:
        # Empty state
        st.info("🔍 **No cards found matching your criteria.**")
        st.markdown("""
        Try adjusting your search or filters:
        - Clear the search box
        - Remove category filters
        - Browse all cards
        """)
        return
    
    st.markdown(f"### 💳 {result_count} Card{'s' if result_count != 1 else ''} Found")
    st.markdown("")
    
    # ========== Modern Card Grid (3 columns) ==========
    # Custom CSS for card styling
    st.markdown("""
    <style>
    .card-container {
        background: white;
        border-radius: 12px;
        padding: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .card-container:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    .card-image {
        width: 100%;
        height: 180px;
        object-fit: cover;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 48px;
        font-weight: bold;
    }
    .card-body {
        padding: 20px;
    }
    .card-provider {
        color: #666;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .card-name {
        font-size: 20px;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 10px;
    }
    .card-badge {
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .reward-item {
        padding: 8px 0;
        border-bottom: 1px solid #f3f4f6;
        font-size: 14px;
    }
    .reward-item:last-child {
        border-bottom: none;
    }
    .reward-multiplier {
        color: #10b981;
        font-weight: bold;
        font-size: 16px;
    }
    .reward-category {
        color: #6b7280;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create 3-column layout
    cols = st.columns(3)
    
    for idx, card in enumerate(filtered_cards):
        with cols[idx % 3]:
            # Get card details
            provider = card['provider']
            card_name = card['card_name']
            base_rate = card.get('base_reward_rate', 1.0)
            image_url = card.get('image_url')
            benefits_url = card.get('benefits_url')
            reward_rules = card.get('reward_rules', [])
            
            # Get best category for badge
            best_category, best_multiplier = get_best_category_for_card(card)
            
            # Card container
            with st.container():
                # Card image or placeholder
                if image_url:
                    st.image(image_url, use_container_width=True)
                else:
                    # Placeholder with provider initial
                    initial = provider[0] if provider else "C"
                    st.markdown(f"""
                    <div class="card-image">
                        {initial}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Card body
                st.markdown(f"""
                <div class="card-body">
                    <div class="card-provider">{provider}</div>
                    <div class="card-name">{card_name}</div>
                    <div class="card-badge">Best: {best_multiplier:.1f}% {best_category}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Reward categories
                if reward_rules:
                    st.markdown("**🎁 Rewards:**")
                    # Show all reward rules (not just top 3)
                    for rule in sorted(reward_rules, key=lambda r: r['multiplier'], reverse=True):
                        bucket = rule['bucket']
                        multiplier = rule['multiplier']
                        icon = get_category_icon(bucket)
                        category_name = bucket.replace('_', ' ').title()
                        
                        st.markdown(f"""
                        <div class="reward-item">
                            <span class="reward-multiplier">{multiplier:.1f}%</span>
                            <span class="reward-category">{icon} {category_name}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"**{base_rate}%** cashback on all purchases")
                
                # Benefits link
                if benefits_url:
                    st.link_button("📖 View Benefits", benefits_url, use_container_width=True)
                else:
                    st.caption("💡 Benefits information coming soon")
                
                st.markdown("<br>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>💳 Card data based on 2026 reward structures</p>
        <p style="font-size: 12px;">Images and benefits information provided by respective card issuers</p>
    </div>
    """, unsafe_allow_html=True)


def identify_cards_page(user_id: str):
    """
    Sprint 1: Card Identification Page
    Allows users to identify their Plaid-synced cards as specific card products.
    
    Args:
        user_id: UUID of the user
    """
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
        # No unidentified cards - all cards are identified!
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
    for idx, user_card in enumerate(unidentified_cards):
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); 
                        padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="margin: 0;">Card #{idx + 1}</h3>
                <p style="margin: 5px 0;"><strong>From Bank:</strong> {user_card['official_name']}</p>
                <p style="margin: 5px 0; font-size: 12px; color: #666;">
                    <strong>Account ID:</strong> {user_card['plaid_account_id'][:20]}...
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create dropdown for card product selection
            card_options = [f"{cp['provider']} - {cp['card_name']}" for cp in card_products]
            card_id_map = {f"{cp['provider']} - {cp['card_name']}": cp['id'] for cp in card_products}
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_card = st.selectbox(
                    "What card is this?",
                    options=card_options,
                    key=f"card_select_{user_card['id']}",
                    help="Select the card product that matches this account"
                )
            
            with col2:
                if st.button("Identify", key=f"btn_{user_card['id']}", type="primary"):
                    # Get the card_product_id
                    card_product_id = card_id_map[selected_card]
                    
                    # Call the identification endpoint
                    with st.spinner("Identifying card..."):
                        success = identify_card(user_card['id'], card_product_id)
                    
                    if success:
                        st.success(f"✅ Successfully identified as **{selected_card}**!")
                        st.info("🔄 Refreshing page in 2 seconds...")
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Failed to identify card. Please try again.")
            
            st.markdown("---")
    
    # Help section
    st.markdown("### ❓ Need Help?")
    st.info("""
    **How to identify your cards:**
    1. Look at the card name shown (from your bank)
    2. Select the matching card product from the dropdown
    3. Click "Identify" to link them
    
    **Don't see your card?** The card might not be in our library yet. Contact support to add it.
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>Your card information is securely linked through Plaid</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main Streamlit application with page navigation."""
    
    # Sidebar Navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["My Dashboard", "Identify My Cards", "Card Discovery"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    
    # User settings (show for Dashboard and Identify pages)
    if page in ["My Dashboard", "Identify My Cards"]:
        st.sidebar.title("⚙️ Settings")
        user_id = st.sidebar.text_input(
            "User ID",
            value="01fe9452-273c-4d3c-aaff-d76b4a5047bb",  # Sprint 1: Updated to test user
            help="Enter the UUID of the user to view their data"
        )
        
        st.sidebar.markdown("---")
        
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
        dashboard_page(user_id)
    elif page == "Identify My Cards":
        identify_cards_page(user_id)
    else:
        card_discovery_page()


if __name__ == "__main__":
    main()

