# Study Platform Documentation

Comprehensive documentation for the Study Platform - a multi-level educational platform with admin course management.

## 📚 Documentation Structure

This documentation is built with [Docusaurus](https://docusaurus.io/), providing a modern, searchable documentation experience for users, admins, and developers.

### Documentation Sections

1. **[User Guide](./docs/user-guide/)** - For students using the platform
2. **[Admin Guide](./docs/admin-guide/)** - For administrators and teachers
3. **[Developer Guide](./docs/developer-guide/)** - For developers contributing to the project
4. **[API Reference](./docs/api/)** - Complete API documentation

## 🚀 Quick Start

### Running the Documentation Locally

```bash
cd docs
npm install
npm start
```

The documentation site will open at `http://localhost:3000`.

### Building for Production

```bash
npm run build
npm run serve
```

## 📖 Documentation Content

### User Guide
- **Getting Started**: Account creation, student level selection
- **Taking Quizzes**: How to take quizzes, view explanations, track scores
- **Student Levels**: Understanding Primary, High School, and Tertiary levels
- **Progress Tracking**: Monitoring your learning progress

### Admin Guide
- **Managing Subjects**: Creating and organizing subjects/courses
- **Managing Categories**: Organizing content within subjects
- **Managing Questions**: Creating, editing, and importing questions
- **Question Banks**: Organizing questions by level and difficulty
- **User Management**: Managing student, teacher, and admin accounts
- **Analytics**: Viewing platform statistics and user progress

### Developer Guide
- **Setup**: Local development environment setup
- **Architecture**: System architecture and design decisions
- **Backend**: FastAPI backend development
- **Frontend**: React + TypeScript frontend development
- **Database**: SQLAlchemy models and migrations
- **Testing**: Unit, integration, and E2E testing
- **Deployment**: Production deployment guide

### API Reference
- **Authentication**: Registration, login, JWT tokens
- **Users**: User management endpoints
- **Subjects**: Subject CRUD operations
- **Categories**: Category CRUD operations
- **Questions**: Question management and bulk operations
- **Quiz**: Quiz session management
- **Progress**: User progress tracking

## 🎯 Key Features Documented

### Multi-Level Student Support
- Primary School (ages 5-11)
- High School (ages 12-18)
- Tertiary/University (college level)

### Role-Based Access Control
- **Students**: Access to age-appropriate content
- **Teachers**: Content creation and management
- **Admins**: Full system access

### Security Features
- BCrypt password hashing
- JWT authentication (access + refresh tokens)
- Rate limiting (60 requests/minute)
- Security headers (HSTS, CSP, X-Frame-Options)
- Input validation and sanitization

### Admin Features
- Subject/Course management
- Category organization
- Question bank management
- Bulk question import
- User management
- Platform analytics

## 📝 Contributing to Documentation

### Adding New Pages

1. Create a new markdown file in the appropriate directory:
   ```
   docs/docs/[section]/[page-name].md
   ```

2. Add frontmatter:
   ```markdown
   ---
   sidebar_position: 1
   ---

   # Page Title

   Page content...
   ```

3. Update `sidebars.js` if needed

### Documentation Style Guide

- Use clear, concise language
- Include code examples with syntax highlighting
- Add screenshots for UI-related documentation
- Use admonitions for important notes:
  ```markdown
  :::tip
  Helpful tip here
  :::

  :::warning
  Important warning
  :::

  :::danger
  Critical information
  :::
  ```

## 🔗 External Resources

- **Repository**: https://github.com/Coded-Shogun/Study-Platform
- **Issue Tracker**: https://github.com/Coded-Shogun/Study-Platform/issues
- **Backend API Docs**: http://localhost:8000/docs (when running locally)

## 📦 Documentation Deployment

### GitHub Pages

```bash
GIT_USER=<Your GitHub username> npm run deploy
```

### Netlify/Vercel

1. Connect your repository
2. Set build command: `cd docs && npm run build`
3. Set publish directory: `docs/build`

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY docs/package*.json ./
RUN npm install
COPY docs/ ./
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
```

## 🛠️ Documentation Maintenance

### Regular Updates

- Update API documentation when endpoints change
- Add new features to user/admin guides
- Update screenshots when UI changes
- Keep setup instructions current
- Review and update examples

### Version Management

Documentation is versioned alongside the codebase. Major releases get dedicated documentation versions:

```bash
npm run docusaurus docs:version 1.0.0
```

## 📧 Support

For documentation issues or suggestions:
- Open an issue: https://github.com/Coded-Shogun/Study-Platform/issues
- Tag with `documentation` label
- Provide specific page/section references

## 📜 License

Documentation is part of the Study Platform project and follows the same license.

---

## 📋 Documentation Checklist

When adding new features, ensure documentation includes:

- [ ] User-facing documentation (if applicable)
- [ ] Admin/Teacher documentation (if applicable)
- [ ] API documentation (for new endpoints)
- [ ] Code examples
- [ ] Screenshots/diagrams (if helpful)
- [ ] Configuration examples
- [ ] Common pitfalls/troubleshooting
- [ ] Related links

## 🎨 Documentation Features

### Supported Features

- ✅ Markdown with MDX support
- ✅ Code syntax highlighting
- ✅ Search functionality
- ✅ Dark/Light theme
- ✅ Version control
- ✅ Internationalization ready
- ✅ Mobile responsive
- ✅ Blog support
- ✅ API documentation
- ✅ Interactive examples

### Planned Enhancements

- [ ] Interactive API playground
- [ ] Video tutorials
- [ ] Interactive diagrams
- [ ] Downloadable PDF guides
- [ ] Multi-language support

## 🏗️ Documentation Structure

```
docs/
├── docs/                      # Documentation content
│   ├── intro.md              # Introduction page
│   ├── user-guide/           # User documentation
│   ├── admin-guide/          # Admin documentation
│   ├── developer-guide/      # Developer documentation
│   └── api/                  # API reference
├── blog/                     # Blog posts
├── src/                      # Custom React components
│   ├── components/           # Reusable components
│   ├── css/                  # Custom styles
│   └── pages/                # Custom pages
├── static/                   # Static assets
│   └── img/                  # Images
├── docusaurus.config.js      # Docusaurus configuration
├── sidebars.js               # Sidebar structure
└── package.json              # Dependencies

```

## 💡 Tips for Users

### Finding Information

- Use the search bar (Ctrl/Cmd + K)
- Check the sidebar navigation
- Browse by category
- Use the "Edit this page" link to suggest improvements

### Reading Code Examples

- Click the copy button to copy code
- Code examples are syntax-highlighted
- Examples are tested and verified

### Getting Help

1. Check the documentation first
2. Search existing issues on GitHub
3. Ask in discussions
4. Open a new issue if needed

---

**Last Updated**: November 2025
**Documentation Version**: 1.0.0
**Platform Version**: 1.0.0
