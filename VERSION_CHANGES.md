# Version Changes

## Version 1.1.0 (April 2025)

### Enhanced Reporting Improvements

1. **Component Analysis Feature**
   - Added TOP AFFECTED COMPONENTS section to reports
   - Provides percentage breakdown of hardware components causing issues
   - Shows up to 12 components sorted by frequency
   - Helps identify patterns in hardware failures across support queues

2. **Expanded High Priority Tickets Display**
   - Increased from 5 to 10 high-priority tickets shown in reports
   - Ensures critical issues are not missed in longer reports
   - Maintained detailed information for each ticket (priority, sentiment, urgency, etc.)

3. **Multi-View Analysis Improvements**
   - Fixed issue with `--view-names` parameter in multi-view mode
   - Now properly supports both view IDs and view names in all modes
   - Enhanced error handling for view name matching
   - Improved view cache refreshing logic

4. **Performance Optimizations**
   - Improved analysis batch processing
   - Enhanced caching mechanisms for view data
   - Added automatic cache refresh for more reliable results

5. **Documentation Updates**
   - Updated ENHANCED_REPORTS.md with latest features
   - Updated MULTI_VIEW.md with new examples and sections
   - Added component analysis documentation

### Bug Fixes

1. Fixed issue where using `--view-names` parameter in multi-view mode would fail
2. Corrected SentimentReporter initialization in multi-view names mode
3. Fixed potential duplicate entries in component analysis
4. Resolved view name matching issues for partial matches
5. Fixed report formatting inconsistencies

### Known Issues

- Very large views (>200 tickets) may cause timeout issues during analysis
- Some partial view name matches may not be intuitive in certain edge cases
- Component names are extracted as-is from ticket analysis and may have inconsistent formatting

### Recommendations

- Use the `--format enhanced` parameter to access all new features
- Consider using view IDs for most reliable results
- For large views, use the `--limit` parameter to restrict the number of tickets processed
