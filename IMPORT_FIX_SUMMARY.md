# Import Path Fix for Shared brains.py Module

**Issue**: `brains.py` is in project root, but chapters need to import it from subdirectories.

**Solution**: Add path fix at the top of each chapter's nanocode.py

## ✅ Working Solution

### Add these lines at the top of each chapter file:

```python
import sys
import os
# Add parent directory to Python path to import brains module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brains import (
    AgentStop,
    Thought,
    Brain,
    Claude,
    DeepSeek,
    ZaiCoding,
    BRAINS
)
```

## 🧪 Verification

Test from ch04 directory:
```bash
cd ch04
python3 nanocode_shared.py
```

## 📁 Alternative Approaches (Not Recommended)

### Option 1: Relative imports
```python
# Doesn't work well with script execution
from ..brains import Claude
```

### Option 2: Install as package
```bash
# Create setup.py and install
pip install -e .
```
**Downside**: More complex, changes project structure

### Option 3: Copy brains.py to each chapter
**Downside**: Defeats purpose of shared module

## ✅ Recommended Approach

Keep the `sys.path.insert(0, '..')` fix - it's:
- Simple and clear
- Works across all chapters
- Standard Python practice for local imports
- Easy to understand and maintain
