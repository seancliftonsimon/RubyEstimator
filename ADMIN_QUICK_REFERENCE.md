# Admin UI Quick Reference Card

## 🎯 Quick Access

**Admin Button Location**: Top-right corner of main page  
**Button Text**: `⚙️ Admin` (click to open) / `✕ Close Admin` (click to close)

## 📋 Admin Tabs Overview

| Tab         | Icon | What It Controls          | # of Values |
| ----------- | ---- | ------------------------- | ----------- |
| Prices      | 💰   | Commodity prices ($/lb)   | 15 items    |
| Costs       | 💵   | Flat costs ($)            | 4 items     |
| Weights     | ⚖️   | Component weights (lbs)   | 9 items     |
| Assumptions | 📊   | Calculation factors (0-1) | 4 items     |
| Heuristics  | 🔍   | Keywords & rules          | 3 items     |
| Grounding   | 🌐   | Search settings           | 5 items     |
| Consensus   | 🤝   | Source preferences        | 6 items     |

## 🔄 Common Actions

### Edit a Value

1. Click `⚙️ Admin`
2. Navigate to the appropriate tab
3. Edit the value(s)
4. Click `💾 Save All Changes`

### Reset a Section

1. Click `⚙️ Admin`
2. Navigate to the tab you want to reset
3. Click `🔄 Restore to Default` (top-right of tab)
4. Click `💾 Save All Changes`

### Reset Everything (Manual Method)

1. Click `⚙️ Admin`
2. Visit each tab and click `🔄 Restore to Default`
3. Click `💾 Save All Changes`

## 🎨 Button Guide

| Button                  | Location                         | Action              |
| ----------------------- | -------------------------------- | ------------------- |
| `⚙️ Admin`              | Top-right corner                 | Opens admin mode    |
| `✕ Close Admin`         | Top-right corner (when in admin) | Closes admin mode   |
| `🔄 Restore to Default` | Top-right of each tab            | Resets that section |
| `💾 Save All Changes`   | Bottom of admin form             | Saves all changes   |

## ⚡ Keyboard Shortcuts

- **Tab**: Navigate between fields
- **Enter**: Submit form (same as clicking Save)
- **Esc**: Not configured (manual close needed)

## 💡 Tips & Tricks

1. **Test Before Saving**: Edit values and test in your head before saving
2. **One Section at a Time**: Focus on one tab to avoid confusion
3. **Restore is Your Friend**: Don't hesitate to use Restore to Default if unsure
4. **Changes Persist**: Once saved, changes remain until you change them again
5. **No Undo**: After clicking Save, there's no undo (use Restore instead)

## 🚨 Common Questions

**Q: Do I need to save after clicking Restore to Default?**  
A: Yes! Restore updates the form, but you still need to click Save.

**Q: Can I restore just one value, not the whole section?**  
A: No, Restore to Default resets the entire section.

**Q: What happens if I edit multiple tabs then click Save?**  
A: All changes across all tabs are saved at once.

**Q: Can I see what changed?**  
A: Not in the UI currently. Check the database directly if needed.

**Q: Is there authentication?**  
A: No, as requested. Anyone can access admin mode.

## 📊 Most Commonly Adjusted

Based on typical usage:

1. **Prices Tab** → CATS (catalytic converter price)
2. **Costs Tab** → PURCHASE (vehicle purchase price)
3. **Prices Tab** → AL_ENGINE (aluminum engine price)
4. **Costs Tab** → TOW (towing cost)
5. **Assumptions Tab** → cats_per_car_default_average

## 🔢 Value Ranges

| Setting      | Min  | Max   | Unit           | Typical Range |
| ------------ | ---- | ----- | -------------- | ------------- |
| Prices       | 0.01 | 1000  | $/lb or $/each | $0.10 - $100  |
| Costs        | 0    | 10000 | $              | $50 - $1000   |
| Weights      | 0.1  | 500   | lbs            | 1 - 100 lbs   |
| Assumptions  | 0.0  | 1.0   | fraction       | 0.1 - 0.9     |
| Cats per car | 0    | 10    | count          | 1 - 3         |

## 🗂️ Database Info

**Table**: `app_config`  
**Keys Stored**:

- `price_per_lb`
- `flat_costs`
- `weights_fixed`
- `assumptions`
- `heuristics`
- `grounding_settings`
- `consensus_settings`

**View Database Values** (SQL):

```sql
SELECT key, description, updated_at, updated_by
FROM app_config
ORDER BY updated_at DESC;
```

## 📝 Default Values (For Reference)

### Critical Prices

- ELV: $0.118/lb
- AL_ENGINE: $0.3525/lb
- CATS: $92.25/lb

### Critical Costs

- PURCHASE: $475
- TOW: $90
- NUT_PER_LB: $0.015/lb

### Critical Assumptions

- engine_weight_percent_of_curb: 0.139 (13.9%)
- cats_per_car_default_average: 1.36

---

**Last Updated**: Implementation Complete  
**Version**: 1.0  
**Status**: ✅ Ready for Use
