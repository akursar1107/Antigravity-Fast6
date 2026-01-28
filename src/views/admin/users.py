"""
Admin Users Tab - User management interface.
Handles adding, viewing, and removing group members.
"""

import streamlit as st
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime
from database import get_all_users, add_user, delete_user


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
    
    # Database Tools Section
    st.markdown("---")
    st.header("🗄️ Database Tools")
    
    col_db1, col_db2 = st.columns(2)
    
    with col_db1:
        st.subheader("Archive Database")
        st.markdown("Create a backup copy of the current database in the archive folder.")
        
        if st.button("📦 Archive Database", key="archive_db_btn", type="primary"):
            try:
                # Database path
                db_path = Path(__file__).parent.parent.parent.parent / "data" / "fast6.db"
                archive_dir = Path(__file__).parent.parent.parent.parent / "archive"
                
                # Create archive directory if it doesn't exist
                archive_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate timestamped filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_path = archive_dir / f"fast6_{timestamp}.db.bak"
                
                # Copy database to archive
                shutil.copy2(db_path, archive_path)
                
                # Get file size for display
                file_size = archive_path.stat().st_size / 1024  # KB
                
                st.success(f"✅ Database archived successfully!")
                st.info(f"📁 Saved to: `{archive_path.name}` ({file_size:.1f} KB)")
                
            except Exception as e:
                st.error(f"❌ Failed to archive database: {str(e)}")
    
    with col_db2:
        st.subheader("Archived Backups")
        try:
            archive_dir = Path(__file__).parent.parent.parent.parent / "archive"
            if archive_dir.exists():
                backups = sorted(
                    [f for f in archive_dir.glob("fast6_*.db.bak")],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                if backups:
                    st.markdown(f"**{len(backups)} backup(s) found:**")
                    for backup in backups[:5]:  # Show last 5
                        size_kb = backup.stat().st_size / 1024
                        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                        st.text(f"📄 {backup.name} ({size_kb:.1f} KB)")
                        st.caption(f"   Created: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if len(backups) > 5:
                        st.caption(f"... and {len(backups) - 5} more")
                else:
                    st.info("No backups found yet.")
            else:
                st.info("Archive directory not found.")
        except Exception as e:
            st.warning(f"Could not read archives: {str(e)}")

    # Danger zone: allow admin to delete the primary picks database
    st.markdown("---")
    st.subheader("🗑️ Danger Zone")
    st.markdown("This will permanently delete the current user picks database file (fast6.db). Archive first.")

    delete_confirm = st.text_input("Type DELETE to confirm", key="delete_db_confirm")
    if st.button("🗑️ Delete User Picks Database", key="delete_db_btn", type="secondary"):
        if delete_confirm.strip().upper() != "DELETE":
            st.warning("Please type DELETE to confirm.")
        else:
            try:
                db_path = Path(__file__).parent.parent.parent.parent / "data" / "fast6.db"
                if db_path.exists():
                    db_path.unlink()
                    st.success("✅ User picks database deleted. Restore from archive if needed.")
                else:
                    st.info("Database file not found; nothing to delete.")
            except Exception as e:
                st.error(f"❌ Failed to delete database: {str(e)}")
