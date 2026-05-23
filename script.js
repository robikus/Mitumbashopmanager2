let display = document.getElementById('display');
let currentInput = '';
let previousValue = '';
let operation = null;
let shouldResetDisplay = false;

// Append number to display
function appendNumber(num) {
    if (shouldResetDisplay) {
        currentInput = num;
        shouldResetDisplay = false;
    } else {
        // Prevent multiple decimal points
        if (num === '.' && currentInput.includes('.')) {
            return;
        }
        currentInput += num;
    }
    updateDisplay();
}

// Append operator
function appendOperator(op) {
    if (currentInput === '') return;
    
    if (operation !== null) {
        calculateResult();
    }
    
    previousValue = currentInput;
    operation = op;
    currentInput = '';
    shouldResetDisplay = true;
}

// Calculate result
function calculateResult() {
    if (operation === null || currentInput === '' || previousValue === '') return;
    
    let result;
    const prev = parseFloat(previousValue);
    const current = parseFloat(currentInput);
    
    switch (operation) {
        case '+':
            result = prev + current;
            break;
        case '-':
            result = prev - current;
            break;
        case '*':
            result = prev * current;
            break;
        case '/':
            if (current === 0) {
                alert('Cannot divide by zero!');
                clearDisplay();
                return;
            }
            result = prev / current;
            break;
        default:
            return;
    }
    
    currentInput = result.toString();
    operation = null;
    previousValue = '';
    shouldResetDisplay = true;
    updateDisplay();
}

// Clear display
function clearDisplay() {
    currentInput = '';
    previousValue = '';
    operation = null;
    shouldResetDisplay = false;
    updateDisplay();
}

// Delete last character
function deleteLast() {
    currentInput = currentInput.toString().slice(0, -1);
    updateDisplay();
}

// Update display
function updateDisplay() {
    display.value = currentInput || '0';
}

// Initialize display
updateDisplay();

// Keyboard support
document.addEventListener('keydown', function(event) {
    if (event.key >= '0' && event.key <= '9') {
        appendNumber(event.key);
    } else if (event.key === '.') {
        appendNumber('.');
    } else if (event.key === '+' || event.key === '-') {
        appendOperator(event.key);
    } else if (event.key === '*') {
        event.preventDefault();
        appendOperator('*');
    } else if (event.key === '/') {
        event.preventDefault();
        appendOperator('/');
    } else if (event.key === 'Enter' || event.key === '=') {
        event.preventDefault();
        calculateResult();
    } else if (event.key === 'Backspace') {
        deleteLast();
    } else if (event.key === 'Escape') {
        clearDisplay();
    }
});