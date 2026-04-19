# Portfolio Website

A modern, responsive portfolio website built with HTML, CSS, and JavaScript for hosting on GitHub Pages.

## 🚀 Features

- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Modern UI**: Clean, professional design with smooth animations and transitions
- **Interactive Elements**: 
  - Smooth scrolling navigation
  - Mobile-friendly hamburger menu
  - Contact form with validation
  - Project cards with hover effects
  - Typing animation for hero title
  - Parallax scrolling effects

## 📁 Project Structure

```
portfolio/
├── index.html          # Main HTML file
├── styles.css          # CSS styling
├── script.js           # JavaScript functionality
└── README.md           # This file
```

## 🛠️ Technologies Used

- **HTML5**: Semantic markup and structure
- **CSS3**: Modern styling with animations and responsive design
- **JavaScript**: Interactive features and form handling
- **Google Fonts**: Inter font family
- **Font Awesome**: Icon library

## 📋 Sections

1. **Hero Section**: Eye-catching introduction with call-to-action buttons
2. **About Section**: Personal information and skills showcase
3. **Projects Section**: Portfolio projects with tech stacks and links
4. **Contact Section**: Contact form and information
5. **Footer**: Social media links and copyright

## 🌐 Deploying to GitHub Pages

### Method 1: Using the existing repository

1. **Push your files to GitHub**:
   ```bash
   git add .
   git commit -m "Add portfolio website"
   git push origin main
   ```

2. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Click on **Settings** tab
   - Scroll down to **GitHub Pages** section
   - Under **Source**, select **Deploy from a branch**
   - Choose **main** branch and **/ (root)** folder
   - Click **Save**

3. **Access your site**:
   - Your site will be available at: `https://yourusername.github.io/repository-name`
   - It may take a few minutes to become available

### Method 2: Using a username.github.io repository

1. **Create a special repository**:
   - Create a new repository named `yourusername.github.io`
   - Make sure it's public
   - Don't initialize with README (since you already have files)

2. **Push your files**:
   ```bash
   git remote set-url origin https://github.com/yourusername/yourusername.github.io.git
   git add .
   git commit -m "Initial portfolio commit"
   git push origin main
   ```

3. **Access your site**:
   - Your site will be available at: `https://yourusername.github.io`
   - This method gives you a cleaner URL without repository name

## ⚙️ Customization

### Personal Information

Edit the following in `index.html`:

1. **Name and Title**:
   ```html
   <h1 class="hero-title">Hi, I'm <span class="highlight">Your Name</span></h1>
   <p class="hero-subtitle">Student & Developer</p>
   ```

2. **About Section**:
   ```html
   <p>I'm a passionate student currently studying...</p>
   ```

3. **Contact Information**:
   ```html
   <div class="contact-item">
       <i class="fas fa-envelope"></i>
       <span>your.email@example.com</span>
   </div>
   ```

### Projects

Update the project cards in the Projects section:

```html
<div class="project-card">
    <div class="project-image">
        <i class="fas fa-code"></i>
    </div>
    <div class="project-content">
        <h3 class="project-title">Your Project Name</h3>
        <p class="project-description">Project description...</p>
        <div class="project-tech">
            <span>Technology 1</span>
            <span>Technology 2</span>
        </div>
        <div class="project-links">
            <a href="https://github.com/yourusername/project" class="project-link">
                <i class="fab fa-github"></i> Code
            </a>
            <a href="https://project-demo.com" class="project-link">
                <i class="fas fa-external-link-alt"></i> Live Demo
            </a>
        </div>
    </div>
</div>
```

### Colors and Styling

Modify `styles.css` to customize:

- **Primary colors**: Change gradient colors in `.hero` and `.skill-tag`
- **Font**: Update Google Fonts import in `index.html`
- **Animations**: Adjust timing and effects in CSS

## 📱 Responsive Design

The website is fully responsive and includes:

- **Mobile navigation** with hamburger menu
- **Flexible grid layouts** that adapt to screen size
- **Touch-friendly** buttons and links
- **Optimized images** and content for mobile devices

## 🎨 Design Features

- **Smooth animations** and transitions
- **Intersection Observer** for scroll animations
- **Parallax effects** on hero section
- **Hover states** on interactive elements
- **Loading animations** for better UX
- **Form validation** with user-friendly notifications

## 🔧 Local Development

1. **Clone or download** the files
2. **Open `index.html`** in your web browser
3. **Or use a local server**:
   ```bash
   # Using Python
   python -m http.server 8000
   
   # Using Node.js (if you have http-server installed)
   npx http-server
   ```
4. **Visit** `http://localhost:8000`

## 📈 Performance Optimization

- **Minified CSS** and JavaScript (for production)
- **Optimized images** (add your own optimized images)
- **Lazy loading** for images (can be implemented)
- **CDN links** for external resources

## 🐛 Troubleshooting

### Common Issues:

1. **GitHub Pages not updating**:
   - Wait up to 10 minutes for changes to propagate
   - Check if you're pushing to the correct branch
   - Verify GitHub Pages is enabled in settings

2. **Styles not loading**:
   - Check file paths in `index.html`
   - Ensure CSS file is named `styles.css`
   - Verify files are in the root directory

3. **JavaScript not working**:
   - Check browser console for errors
   - Ensure `script.js` is loaded after HTML content
   - Verify no syntax errors in JavaScript

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

Feel free to fork this project and customize it for your own portfolio!

## 📞 Support

If you encounter any issues or have questions, feel free to open an issue on GitHub.

---

**Happy coding! 🎉**
