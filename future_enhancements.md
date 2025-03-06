# Future Enhancements for Z

## Multi-Format Storage System
- Implement a storage manager that handles multiple data formats
- Use JSON as primary storage for hierarchical data and relationships
- Add converters for CSV (tabular analysis), plain text (portability), and HTML (rich presentation)
- Design a plugin architecture for adding new storage formats
- Ensure backward compatibility for existing notes

Priority: Medium
Estimated Complexity: High
Dependencies: None

## Flexible Token Ranking System
- Implement a system for ranking tokens along specified axes/dimensions
- Allow tokens to be grouped into sets when their relative ranking is uncertain
- Support partial ordering (e.g., knowing B > {A,C} without knowing if A > C)
- Enable ranking groups themselves, not just individual tokens
- Allow rankings to evolve over time as more information becomes available
- Visualization tools to display current hierarchy of groups and tokens
- Search/filter capabilities based on ranking position

Priority: Medium
Implementation Complexity: Complex
Dependencies: None