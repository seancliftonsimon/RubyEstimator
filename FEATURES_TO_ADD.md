# Ruby Estimator - Features to Add

This document outlines planned features and improvements for the Ruby Estimator application. Each feature includes a brief description and a simple implementation method focused on minimal disruption to existing functionality.

---

## 1. Input Cleaning and Standardization

**Functionality Needed:**

- Automatically clean and standardize user inputs for year, make, and model fields
- Remove extra whitespace, normalize formatting
- Ensure consistent data entry across all searches

**Implementation Method:**

- Create a simple `sanitize_input(text)` helper function that applies `.strip()`, converts multiple spaces to single spaces, and standardizes formatting
- Apply this function to all inputs before database lookups or comparisons
- Add this as a wrapper around existing input fields without changing core logic

---

## 2. Searchable Dropdown with Custom Entry

**Functionality Needed:**

- Provide dropdown options for year, make, and model that filter as earlier fields are filled
- Allow users to type custom entries if their vehicle isn't in the dropdown
- Make and model dropdowns should update dynamically based on previous selections

**Implementation Method:**

- Use Streamlit's `st.selectbox` with dynamically generated options based on database query results
- Add an "Other (type custom)" option at the end of each dropdown
- When "Other" is selected, show a text input field using `st.text_input`
- Query the database to filter available makes by selected year, and models by selected year+make

---

## 3. Case Correction and Normalization

**Functionality Needed:**

- Prevent different capitalizations or spacing variations from being treated as separate vehicles
- Standardize entries like "Honda", "HONDA", and "honda" to match the same database record
- Apply consistently across search, display, and admin functions

**Implementation Method:**

- Extend the `sanitize_input()` function to include `.title()` or `.upper()` case conversion
- Apply case normalization before all database queries using a SQL `UPPER()` or `LOWER()` comparison
- Store a normalized version alongside the display version in the database (e.g., `make_normalized` column)

---

## 4. Unit Conversion - Kilogram Warning

**Functionality Needed:**

- Ensure weight values entered in kilograms are not mistakenly treated as pounds
- Properly convert between units throughout the application
- Maintain consistency from user input through database storage and calculations

**Implementation Method:**

- Add a radio button or dropdown next to weight input: "Unit: [Pounds | Kilograms]"
- If kilograms selected, multiply by 2.20462 to convert to pounds before storing/calculating
- Display a clear label showing which unit is currently being used
- Store all weights in the database in a single standard unit (pounds) with conversion happening at input/output only

---

## 5. Better Error Reporting for Car Lookup Failures

**Functionality Needed:**

- Provide specific, helpful error messages when a car is not found
- Distinguish between different types of lookup failures (year mismatch, wrong manufacturer, etc.)
- Suggest common solutions to users

**Implementation Method:**

- Create an error checking function that queries the database in stages: check if make exists, then if model exists for that make, then if year exists for that model
- Return specific error messages based on which stage fails:
  - "That model was not made in [year]. Available years: [list]"
  - "[Model] is not made by [Make]. Did you mean [suggested make]?"
  - "Vehicle not found. Please check spelling or use the dropdown."
- Display errors using `st.error()` or `st.warning()` with actionable information

---

## 6. Global and Permanent Admin Changes

**Functionality Needed:**

- Ensure admin modifications to vehicle data persist across sessions
- Changes should be immediately reflected for all users
- Maintain a history of admin changes for accountability

**Implementation Method:**

- Create a new database table `admin_overrides` with columns: `vehicle_id`, `field_name`, `new_value`, `modified_by`, `modified_date`
- When admin makes a change, INSERT or UPDATE into this table
- Modify the main query function to JOIN with `admin_overrides` and prefer override values when present
- Add a simple `st.success("Changes saved permanently")` confirmation message

---

## 7. Button to Revert Admin Changes

**Functionality Needed:**

- Allow admins to undo their modifications and restore original values
- Provide a clear way to see what has been changed
- Make reversion simple and non-destructive

**Implementation Method:**

- Add a "Revert to Original" button next to each admin-edited field
- Store original values in the `admin_overrides` table with an `is_active` flag
- Set `is_active = FALSE` when reverting instead of deleting the record (preserves history)
- Use `st.button()` with a confirmation step using `st.warning()` before reverting

---

## 8. Preserve All Vehicle Values in Same Database Table

**Functionality Needed:**

- Ensure all attributes for a vehicle (weight, year, make, model, etc.) are stored together
- Avoid data fragmentation across multiple tables
- Simplify queries and reduce join complexity

**Implementation Method:**

- Audit current database schema to identify any split data
- If data is fragmented, create a migration script to consolidate into a single `vehicles` table
- Use a single SELECT query with all needed columns rather than multiple queries
- Add any missing columns to the main table and populate from other sources

---

## 9. Fix Ghosting Issue When Searching New Car

**Functionality Needed:**

- Completely remove previous vehicle information and visual components when a new search is performed
- Prevent old results from appearing faded or partially visible below new results
- Ensure clean state between searches

**Implementation Method:**

- Clear session state for previous results before displaying new ones: `st.session_state.pop('previous_results', None)`
- Use `st.empty()` containers to hold results, and call `.empty()` method before rendering new content
- Alternatively, use a unique `key` parameter in Streamlit components that changes with each search (e.g., `key=f"result_{timestamp}"`)
- Add a `st.rerun()` call after clearing if ghosting persists

---

## 10. Move Title to Bottom and Make Smaller

**Functionality Needed:**

- Relocate the "Ruby G.E.M." title from the top of the page to the bottom
- Reduce the title size to minimize screen space usage
- Maximize visible space for the main application functionality

**Implementation Method:**

- Move the title code (likely `st.title()` or `st.header()`) to the end of the main script
- Change from `st.title()` to `st.caption()` or use `st.markdown()` with smaller HTML heading: `st.markdown("#### Ruby G.E.M.")`
- Optionally add horizontal rule before title: `st.divider()` followed by small centered text
- Consider adding it to a footer-style container with gray or muted color

---

## Implementation Priority

**Recommended order for implementation:**

1. **Fix Ghosting Issue** - Quick fix, improves UX immediately
2. **Move Title to Bottom** - Simple layout change, improves screen real estate
3. **Input Cleaning and Standardization** - Foundation for other features
4. **Case Correction** - Builds on standardization, prevents duplicate entries
5. **Better Error Reporting** - Improves user experience significantly
6. **Searchable Dropdown** - Larger feature, but high value for users
7. **Unit Conversion Warning** - Important for data accuracy
8. **Global Admin Changes** - Requires database work but critical for admin functionality
9. **Revert Admin Changes** - Extension of admin functionality
10. **Preserve Values in Same Table** - Database optimization, lower priority if current system works

---

## Testing Notes

For each feature:

- Test with existing functionality to ensure no regressions
- Verify database queries still return correct results
- Check that the app passes the 90% accuracy requirement (9/10 tests)
- Test both local and online deployments
- Verify admin backend continues to function correctly
