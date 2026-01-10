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


def main():
    """Main Streamlit application."""
    
    # Sidebar: User Selection
    st.sidebar.title("⚙️ Settings")
    st.sidebar.markdown("---")
    
    # User ID Input
    user_id = st.sidebar.text_input(
        "User ID",
        value="4b0939d1-7595-414e-bbd9-597f41c39e99",
        help="Enter the UUID of the user to view their savings report"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 💡 About
    This dashboard shows your credit card cashback optimization insights:
    - **Total Spent**: Your transaction volume
    - **Actual Rewards**: Cashback you earned
    - **Lost Savings**: Opportunity cost from suboptimal card usage
    """)
    
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


if __name__ == "__main__":
    main()

