# XenShoot Changelog

## Version 2.0.0 - BackBlaze B2 Integration

### Major Changes
- ✅ **BackBlaze B2 Storage**: Direct upload to your own cloud storage
- ✅ **Pre-configured Credentials**: Ready to use out of the box
- ✅ **S3-Compatible API**: Fast and reliable uploads
- ✅ **Cleaned Codebase**: Removed all test and debug files

### New Features
- BackBlaze B2 uploader with S3-compatible API
- Automatic public URL generation
- Support for custom bucket configuration
- Direct file upload without third-party services

### Improvements
- Simplified upload service selection
- BackBlaze B2 set as default service
- Updated settings UI with BackBlaze configuration
- Better error handling and user feedback

### Removed
- All test files (test_*.py)
- Debug and setup scripts
- Obsolete documentation files
- Dashboard integration (not needed with direct storage)

### Technical Details
- Using boto3 for S3-compatible uploads
- Public-read ACL for direct URL access
- Organized storage in `screenshots/` folder
- Timestamp-based filename generation

---

## Version 1.2.2 - UI Polish

- Improved annotation toolbar
- Better color picker
- Smoother drawing experience
- Bug fixes for multi-monitor support

## Version 1.2.1 - UI Fixes

- Fixed overlay crash on certain displays
- Improved screenshot quality
- Better hotkey handling

## Version 1.2.0 - Multiple Upload Services

- Added Cloudinary support
- Added Imgur support
- Added ImgBB support
- Custom endpoint option

## Version 1.1.0 - Annotation Tools

- Rectangle, circle, arrow tools
- Line and pen tools
- Text annotation
- Blur tool for sensitive info
- Undo functionality

## Version 1.0.0 - Initial Release

- Area screenshot capture
- Fullscreen screenshot
- Global hotkeys
- System tray integration
- Auto-copy URL to clipboard
- Local file saving option

---

**Current Version: 2.0.0** - BackBlaze B2 Integration
