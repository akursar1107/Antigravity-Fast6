# UI Design Principles - Fast6

**Date:** January 27, 2026  
**Purpose:** Document design decisions and rationale

---

## 🎯 Core Principles

### 1. **Clarity Over Cleverness**
- Simple, obvious interactions beat clever, hidden ones
- Users should never wonder "how do I...?"
- Every element should have a clear purpose

### 2. **Function Over Form**
- Usability comes before aesthetics
- Remove any visual element that doesn't serve a purpose
- Performance matters more than visual flair

### 3. **Consistency is King**
- Same patterns throughout the app
- Predictable behavior
- Muscle memory development

### 4. **Mobile-First Thinking**
- Design for smallest screen first
- Touch targets minimum 44px
- Readable text without zooming

### 5. **Accessibility Matters**
- High contrast ratios (WCAG AA minimum)
- Keyboard navigation support
- Screen reader friendly

---

## 🎨 Color Usage Guide

### Primary Color (`#5B8FF9` - Vibrant Blue)
**Use for:**
- Active states
- Primary actions
- Selected items
- Links

**Don't use for:**
- Backgrounds (too bright)
- Body text (readability)

### Accent Color (`#FF6B6B` - Coral Red)
**Use for:**
- Call-to-action buttons
- Attention-grabbing elements
- Delete/destructive actions
- Errors

**Don't use for:**
- Success messages
- Large areas

### Success Color (`#51CF66` - Bright Green)
**Use for:**
- Success messages
- Positive metrics (wins, gains)
- Confirmation states

**Don't use for:**
- Errors or warnings
- Neutral information

### Warning Color (`#FFA94D` - Orange)
**Use for:**
- Warning messages
- Pending states
- Caution indicators

**Don't use for:**
- Success or error states

### Background Colors
- **True Dark:** `#0F1419` - Main background
- **Surface:** `#1A2332` - Cards, elevated elements
- **Border:** `#2D3748` - Subtle separators

---

## 📐 Spacing System

### Padding Scale
- **xs:** 0.25rem (4px)
- **sm:** 0.5rem (8px)
- **md:** 1rem (16px)
- **lg:** 1.5rem (24px)
- **xl:** 2rem (32px)
- **2xl:** 3rem (48px)

### Margin Scale
Same as padding scale

### Border Radius
- **Standard:** 8px (consistent throughout)
- **Small:** 4px (badges, small elements)
- **Large:** 12px (modals, large cards)

---

## ✍️ Typography Scale

### Font Family
- **Primary:** Inter (body text, UI)
- **Monospace:** Roboto Mono (numbers, code)

### Size Scale
- **H1:** 2.5rem (40px) - Page titles
- **H2:** 1.75rem (28px) - Section headers
- **H3:** 1.25rem (20px) - Subsection headers
- **Body:** 1rem (16px) - Default text
- **Small:** 0.875rem (14px) - Captions, meta
- **Tiny:** 0.75rem (12px) - Labels, badges

### Weight Scale
- **Regular:** 400 - Body text
- **Medium:** 500 - Emphasis
- **Semibold:** 600 - Subheadings
- **Bold:** 700 - Headings

---

## 🧩 Component Guidelines

### Buttons
- **Primary:** Blue background, white text
- **Secondary:** Transparent background, blue border
- **Destructive:** Red background, white text
- **Minimum height:** 44px (mobile touch target)
- **Padding:** 0.6rem 1.75rem

### Cards
- **Background:** `#1A2332` (Surface)
- **Border:** 1px solid `#2D3748`
- **Radius:** 8px
- **Shadow:** `0 2px 8px rgba(0, 0, 0, 0.3)`
- **No blur effects**

### Tables
- **Header background:** `#1A2332`
- **Header text:** Primary blue
- **Row hover:** Slight background change
- **Borders:** Subtle `#2D3748`
- **Alternating rows:** Slight background difference

### Tabs
- **Background:** `#1A2332`
- **Active:** Primary blue background
- **Inactive:** Transparent, gray text
- **Border radius:** 8px
- **Padding:** 10px 20px

### Metrics/Stats
- **Background:** `#1A2332`
- **Border left:** 4px solid primary blue
- **Label:** Gray, uppercase, small
- **Value:** Primary blue, large, monospace

---

## 🚫 What to Avoid

### Visual Effects
- ❌ Glassmorphism / backdrop-filter blur
- ❌ Gradient text
- ❌ Excessive shadows
- ❌ Animations without purpose
- ❌ Parallax scrolling
- ❌ Auto-playing videos

### Layout
- ❌ Fixed widths (use responsive)
- ❌ Horizontal scrolling
- ❌ Too many columns (5 max for tables)
- ❌ Nested dropdowns
- ❌ Hidden navigation

### Colors
- ❌ Low contrast text
- ❌ Pure black backgrounds
- ❌ Too many accent colors
- ❌ Neon colors
- ❌ Gradient backgrounds

### Typography
- ❌ More than 2 font families
- ❌ Text smaller than 14px
- ❌ All caps for long text
- ❌ Centered body text
- ❌ Justified text

---

## ✅ Best Practices

### Navigation
1. **Always visible** - No hidden menus
2. **One level deep** - Avoid nested navigation
3. **Clear labels** - No clever names
4. **Active state** - Always show where you are

### Forms
1. **Labels above inputs** - Not inside
2. **Clear validation** - Immediate feedback
3. **Error messages** - Specific, helpful
4. **Submit buttons** - Always visible

### Data Display
1. **Progressive disclosure** - Overview → Details
2. **Scannable** - Can understand in < 5 seconds
3. **Sortable/Filterable** - User control
4. **Pagination** - For large datasets

### Performance
1. **Lazy loading** - Load what's needed
2. **Image optimization** - Compressed, sized correctly
3. **Minimal dependencies** - Only what's necessary
4. **Caching** - Reduce redundant requests

---

## 📱 Mobile Considerations

### Breakpoints
- **Mobile:** < 768px
- **Tablet:** 768px - 1024px
- **Desktop:** > 1024px

### Mobile-Specific Rules
1. **Single column layouts**
2. **Larger touch targets** (44px minimum)
3. **Simplified navigation** (hamburger menu)
4. **Fewer columns in tables** (3-4 max)
5. **Larger text** (16px minimum)
6. **No hover states** (use active states)

---

## 🔍 Testing Checklist

### Visual Testing
- [ ] Check all pages in Chrome, Firefox, Safari
- [ ] Test on iPhone SE (smallest common screen)
- [ ] Test on iPad (mid-size)
- [ ] Test on 1920px desktop
- [ ] Verify color contrast (WCAG AA)
- [ ] Check dark mode (if applicable)

### Interaction Testing
- [ ] All buttons clickable
- [ ] All links work
- [ ] Forms validate correctly
- [ ] Navigation works on all pages
- [ ] Keyboard navigation works
- [ ] Screen reader announces correctly

### Performance Testing
- [ ] Lighthouse score > 90
- [ ] Page load < 3 seconds
- [ ] No layout shift (CLS < 0.1)
- [ ] Smooth scrolling (60fps)
- [ ] No memory leaks

---

## 📚 Resources

### Design Systems
- [Material Design](https://material.io/design)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Tailwind CSS](https://tailwindcss.com/)

### Color Tools
- [Coolors](https://coolors.co/) - Color palette generator
- [Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Adobe Color](https://color.adobe.com/)

### Typography
- [Google Fonts](https://fonts.google.com/)
- [Type Scale](https://type-scale.com/)
- [Modular Scale](https://www.modularscale.com/)

### Accessibility
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [A11y Project](https://www.a11yproject.com/)
- [WebAIM](https://webaim.org/)

---

**Remember:** Good design is invisible. Users should accomplish their goals without noticing the interface.
