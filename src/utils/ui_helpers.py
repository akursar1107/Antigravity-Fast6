"""
UI Helper Functions
Reusable UI components and formatting utilities for Streamlit.
"""

import streamlit as st
from typing import Optional, Literal


def status_badge(
    status: Literal['correct', 'incorrect', 'pending', 'graded', 'missing', 'warning'],
    text: Optional[str] = None
) -> str:
    """
    Generate a colored status badge for display.
    
    Args:
        status: Status type
        text: Optional custom text (defaults based on status)
    
    Returns:
        Formatted badge string with emoji and color
    
    Example:
        >>> st.markdown(status_badge('correct', 'Win!'))
        >>> st.markdown(status_badge('pending'))
    """
    badges = {
        'correct': {'emoji': '✅', 'text': text or 'Correct', 'color': 'green'},
        'incorrect': {'emoji': '❌', 'text': text or 'Incorrect', 'color': 'red'},
        'pending': {'emoji': '⏳', 'text': text or 'Pending', 'color': 'orange'},
        'graded': {'emoji': '✅', 'text': text or 'Graded', 'color': 'green'},
        'missing': {'emoji': '⚠️', 'text': text or 'Missing', 'color': 'orange'},
        'warning': {'emoji': '⚠️', 'text': text or 'Warning', 'color': 'orange'},
    }
    
    badge = badges.get(status, {'emoji': '❓', 'text': text or 'Unknown', 'color': 'gray'})
    
    return f"{badge['emoji']} **{badge['text']}**"


def metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    help_text: Optional[str] = None
) -> None:
    """
    Display a metric card with optional delta and help text.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta/change indicator
        help_text: Optional help tooltip
    
    Example:
        >>> metric_card("Total Users", "42", "+5 this week", "Active users")
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        help=help_text
    )


def info_box(
    title: str,
    content: str,
    box_type: Literal['info', 'success', 'warning', 'error'] = 'info'
) -> None:
    """
    Display a styled information box.
    
    Args:
        title: Box title
        content: Box content
        box_type: Type of box (determines color/icon)
    
    Example:
        >>> info_box("Success", "Operation completed", "success")
    """
    icons = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }
    
    icon = icons.get(box_type, 'ℹ️')
    message = f"**{icon} {title}**\n\n{content}"
    
    if box_type == 'error':
        st.error(message)
    elif box_type == 'warning':
        st.warning(message)
    elif box_type == 'success':
        st.success(message)
    else:
        st.info(message)


def progress_indicator(
    current: int,
    total: int,
    label: Optional[str] = None,
    show_percentage: bool = True
) -> None:
    """
    Display a progress bar with optional label.
    
    Args:
        current: Current progress value
        total: Total/target value
        label: Optional label text
        show_percentage: Whether to show percentage
    
    Example:
        >>> progress_indicator(48, 60, "Picks Submitted")
    """
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100
    
    text = label or f"{current}/{total}"
    if show_percentage:
        text += f" ({percentage:.1f}%)"
    
    st.progress(percentage / 100, text=text)


def confirmation_button(
    label: str,
    key: str,
    confirmation_text: str = "Click again to confirm",
    button_type: Literal['primary', 'secondary'] = 'secondary',
    disabled: bool = False
) -> bool:
    """
    Create a button that requires two clicks to confirm action.
    
    Args:
        label: Button label
        key: Unique key for button
        confirmation_text: Text to show on first click
        button_type: Button style
        disabled: Whether button is disabled
    
    Returns:
        True if action is confirmed (second click), False otherwise
    
    Example:
        >>> if confirmation_button("Delete", "delete_btn"):
        ...     perform_delete()
    """
    confirm_key = f"{key}_confirm"
    
    if st.button(label, key=key, type=button_type, disabled=disabled):
        if st.session_state.get(confirm_key) != True:
            st.session_state[confirm_key] = True
            st.warning(f"⚠️ {confirmation_text}")
            return False
        else:
            # Confirmed
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            return True
    
    return False


def data_table_with_status(
    df,
    status_column: str = 'status',
    status_mapping: Optional[dict] = None
) -> None:
    """
    Display a dataframe with colored status indicators.
    
    Args:
        df: DataFrame to display
        status_column: Name of column containing status
        status_mapping: Optional mapping of status values to badge types
    
    Example:
        >>> data_table_with_status(picks_df, 'is_correct')
    """
    if status_mapping is None:
        status_mapping = {
            True: 'correct',
            False: 'incorrect',
            None: 'pending',
            'correct': 'correct',
            'incorrect': 'incorrect',
            'pending': 'pending'
        }
    
    # Create a copy to avoid modifying original
    display_df = df.copy()
    
    # Replace status column with badges
    if status_column in display_df.columns:
        display_df[status_column] = display_df[status_column].apply(
            lambda x: status_badge(status_mapping.get(x, 'pending'))
        )
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def quick_action_buttons(actions: list) -> Optional[str]:
    """
    Display a row of quick action buttons.
    
    Args:
        actions: List of dicts with keys: label, key, icon (optional)
    
    Returns:
        Key of clicked button, or None
    
    Example:
        >>> actions = [
        ...     {'label': 'Grade All', 'key': 'grade', 'icon': '🎯'},
        ...     {'label': 'Import', 'key': 'import', 'icon': '📥'}
        ... ]
        >>> clicked = quick_action_buttons(actions)
        >>> if clicked == 'grade':
        ...     grade_all_picks()
    """
    cols = st.columns(len(actions))
    
    for idx, action in enumerate(actions):
        with cols[idx]:
            icon = action.get('icon', '')
            label = f"{icon} {action['label']}" if icon else action['label']
            
            if st.button(label, key=action['key'], use_container_width=True):
                return action['key']
    
    return None
