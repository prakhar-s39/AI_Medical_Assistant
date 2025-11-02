// Configuration - Automatically detect API URL from current page origin
// The API runs on the same server, so we use the same origin
const API_BASE_URL = window.location.origin;
const API_ENDPOINT = `${API_BASE_URL}/ask`;

// Initialize background animation
function initBackgroundAnimation() {
    const container = document.getElementById('backgroundAnimation');
    
    // Create multiple pulsing circles
    for (let i = 0; i < 6; i++) {
        const circle = document.createElement('div');
        circle.style.position = 'absolute';
        circle.style.width = `${100 + i * 50}px`;
        circle.style.height = `${100 + i * 50}px`;
        circle.style.borderRadius = '50%';
        circle.style.background = `rgba(255, 255, 255, ${0.05 + i * 0.02})`;
        circle.style.filter = 'blur(40px)';
        
        // Random initial position
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        circle.style.left = `${x}%`;
        circle.style.top = `${y}%`;
        
        container.appendChild(circle);
        
        // Animate with anime.js
        anime({
            targets: circle,
            translateX: [
                { value: anime.random(-200, 200), duration: anime.random(3000, 5000) },
                { value: anime.random(-200, 200), duration: anime.random(3000, 5000) }
            ],
            translateY: [
                { value: anime.random(-200, 200), duration: anime.random(3000, 5000) },
                { value: anime.random(-200, 200), duration: anime.random(3000, 5000) }
            ],
            scale: [
                { value: anime.random(0.8, 1.2), duration: anime.random(2000, 4000) },
                { value: anime.random(0.8, 1.2), duration: anime.random(2000, 4000) }
            ],
            opacity: [
                { value: anime.random(0.05, 0.15), duration: anime.random(2000, 4000) },
                { value: anime.random(0.05, 0.15), duration: anime.random(2000, 4000) }
            ],
            easing: 'easeInOutSine',
            loop: true,
            direction: 'alternate'
        });
    }
}

// Submit query to API
async function submitQuery() {
    const queryInput = document.getElementById('medicalQuery');
    const query = queryInput.value.trim();
    
    if (!query) {
        alert('Please enter a medical question.');
        return;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('submitBtn');
    const buttonText = submitBtn.querySelector('.button-text');
    const loader = document.getElementById('loader');
    
    buttonText.textContent = 'Processing...';
    loader.style.display = 'flex';
    submitBtn.disabled = true;
    
    // Hide previous results
    document.getElementById('responseSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    
    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        displayError(`Failed to get response: ${error.message}. Make sure the server is running at ${API_BASE_URL}`);
    } finally {
        // Reset button state
        buttonText.textContent = 'Ask Question';
        loader.style.display = 'none';
        submitBtn.disabled = false;
    }
}

// Display results in cards
function displayResults(data) {
    const responseSection = document.getElementById('responseSection');
    
    // Update content
    document.getElementById('diagnosisContent').textContent = data.diagnosis || 'No diagnosis provided.';
    document.getElementById('adviceContent').textContent = data.advice || 'No advice provided.';
    
    // Update confidence with badge
    const confidence = (data.confidence || 'medium').toLowerCase();
    const confidenceContent = document.getElementById('confidenceContent');
    confidenceContent.innerHTML = `<span class="confidence-badge confidence-${confidence}">${confidence}</span>`;
    
    // Show response section
    responseSection.style.display = 'grid';
    
    // Animate cards with anime.js
    anime({
        targets: '.card',
        opacity: [0, 1],
        translateY: [30, 0],
        delay: anime.stagger(100),
        duration: 600,
        easing: 'easeOutExpo'
    });
    
    // Scroll to results
    responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Display error message
function displayError(message) {
    const errorSection = document.getElementById('errorSection');
    document.getElementById('errorMessage').textContent = message;
    errorSection.style.display = 'block';
    
    // Animate error card
    anime({
        targets: '.error-card',
        opacity: [0, 1],
        scale: [0.9, 1],
        duration: 400,
        easing: 'easeOutExpo'
    });
    
    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Allow Enter key to submit (Shift+Enter for new line)
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('medicalQuery');
    
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitQuery();
        }
    });
    
    // Initialize background animation
    initBackgroundAnimation();
    
    // Check API health on load
    checkAPIHealth();
});

// Check if API is available
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        if (response.ok) {
            console.log('✅ API is available');
        }
    } catch (error) {
        console.warn('⚠️ API health check failed:', error.message);
        console.info(`API endpoint: ${API_BASE_URL}`);
    }
}

