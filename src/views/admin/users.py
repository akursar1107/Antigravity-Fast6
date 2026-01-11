"""
Admin Users Tab - User management interface.
Handles adding, viewing, and removing group members.
"""

import streamlit as st
import pandas as pd
from utils import get_all_users, add_user, delete_user


def show_users_tab() -> None:
    """Display and manage users in the admin panel."""
    st.header("👥 Group Member Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add New Member")
        new_name = st.text_input("Member Name", placeholder="e.g., John")
        new_email = st.text_input("Email (optional)", placeholder="e.g., john@example.com")
        
        if st.button("Add Member", key="add_user_btn"):
            if new_name.strip():
                try:
                    user_id = add_user(new_name.strip(), new_email if new_email else None)
                    st.success(f"✅ Added {new_name} (ID: {user_id})")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
            else:
                st.warning("Please enter a name")
    
    with col2:
        st.subheader("Current Members")
        users = get_all_users()
        
        if users:
            users_df = pd.DataFrame(users)
            st.dataframe(
                users_df[['id', 'name', 'email', 'created_at']],
                width='stretch',
                hide_index=True
            )
            
            st.markdown("---")
            st.subheader("Remove Member")
            user_to_remove = st.selectbox(
                "Select member to remove",
                options=users,
                format_func=lambda x: x['name'],
                key="remove_user_select"
            )
            
            if st.button("Delete Member", key="delete_user_btn", type="secondary"):
                if delete_user(user_to_remove['id']):
                    st.success(f"✅ Removed {user_to_remove['name']}")
                    st.rerun()
        else:
            st.info("No members yet. Add one to get started!")
