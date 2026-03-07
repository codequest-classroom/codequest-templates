# 🚀 {{mission.title}}

## 👋 Hey {{student.name}}!

### 📚 Quick Tutorial

<details>
<summary>📖 Click to open tutorial</summary>

### What you'll learn:
{{mission.description}}

### Step-by-Step:
{{#each mission.tutorial}}
{{this}}
{{/each}}

### Example:
```html
{{mission.example}}
