// Initialize PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.10.377/pdf.worker.min.js';

// Sample data structure for the Sankey diagram
let sankeyData = {
    nodes: [],
    links: []
};

// Function to process the uploaded PDF
function processPDF() {
    const fileInput = document.getElementById('pdf-upload');
    const file = fileInput.files[0];
    
    // Enhanced file validation
    if (!file) {
        addUploadStatus('Please select a file to upload.');
        return;
    }
    
    if (file.type !== 'application/pdf') {
        addUploadStatus('Please upload a valid PDF file. Other file types are not supported.');
        return;
    }
    
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        addUploadStatus('File size exceeds the maximum limit of 10MB. Please choose a smaller file.');
        return;
    }
    
    addUploadStatus('Processing your PDF file...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Get the base URL dynamically (works both locally and when deployed)
    const baseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:5000' 
        : window.location.origin;
        
    fetch(`${baseUrl}/api/process-pdf`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Server error: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Parse the financial data from the response
        const financialData = data.data;
        
        // Store the financial data for chat functionality
        window.lastProcessedData = financialData;
        
        // Validate required data structure
        if (!financialData || !financialData.income_statement || !financialData.balance_sheet) {
            throw new Error('Invalid data structure received from server');
        }
        
        // Prepare data for Sankey diagram based on diagram type
        const diagramType = document.getElementById('diagram-type').value;
        
        let incomeCategories = [];
        let expenseCategories = [];
        let assetCategories = [];
        let liabilityCategories = [];
        let equityCategories = [];
        let transactions = [];
        
        if (diagramType === 'balance-sheet') {
            // Process Balance Sheet data with subsections
            assetCategories = [
                ...financialData.balance_sheet.assets.current.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'asset',
                    subcategory: 'current'
                })),
                ...financialData.balance_sheet.assets.non_current.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'asset',
                    subcategory: 'non_current'
                }))
            ];
            
            liabilityCategories = [
                ...financialData.balance_sheet.liabilities.current.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'liability',
                    subcategory: 'current'
                })),
                ...financialData.balance_sheet.liabilities.non_current.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'liability',
                    subcategory: 'non_current'
                }))
            ];
            
            equityCategories = financialData.balance_sheet.equity.map(item => ({
                name: item.name,
                value: item.value,
                type: 'equity'
            }));
        } else {
            // Process P&L data with subsections
            incomeCategories = [
                ...financialData.income_statement.revenue.operating.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'income',
                    subcategory: 'operating'
                })),
                ...financialData.income_statement.revenue.non_operating.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'income',
                    subcategory: 'non_operating'
                }))
            ];
            
            expenseCategories = [
                ...financialData.income_statement.expenses.operating.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'expense',
                    subcategory: 'operating'
                })),
                ...financialData.income_statement.expenses.non_operating.map(item => ({
                    name: item.name,
                    value: item.value,
                    type: 'expense',
                    subcategory: 'non_operating'
                }))
            ];
        }
        
        // Create transactions based on the financial data
        if (diagramType === 'balance-sheet') {
            // Connect liabilities and equity to total assets
            const totalAssets = assetCategories.reduce((sum, asset) => sum + asset.value, 0);
            liabilityCategories.forEach(liability => {
                transactions.push({
                    source: liability.name,
                    target: 'Total Assets',
                    value: liability.value
                });
            });
            equityCategories.forEach(equity => {
                transactions.push({
                    source: equity.name,
                    target: 'Total Assets',
                    value: equity.value
                });
            });
            // Connect total assets to individual assets
            assetCategories.forEach(asset => {
                transactions.push({
                    source: 'Total Assets',
                    target: asset.name,
                    value: asset.value
                });
            });
        } else {
            // Connect revenue to expenses and profit
            const totalRevenue = incomeCategories.reduce((sum, income) => sum + income.value, 0);
            const totalExpenses = expenseCategories.reduce((sum, expense) => sum + expense.value, 0);
            const profit = totalRevenue - totalExpenses;
            
            incomeCategories.forEach(income => {
                transactions.push({
                    source: income.name,
                    target: 'Total Revenue',
                    value: income.value
                });
            });
            transactions.push({
                source: 'Total Revenue',
                target: 'Costs',
                value: totalExpenses
            });
            transactions.push({
                source: 'Total Revenue',
                target: 'Profit',
                value: profit > 0 ? profit : 0
            });
            expenseCategories.forEach(expense => {
                transactions.push({
                    source: 'Costs',
                    target: expense.name,
                    value: expense.value
                });
            });
        }
        
        // Prepare and draw the Sankey diagram
        prepareSankeyData(
            incomeCategories,
            expenseCategories,
            transactions,
            assetCategories,
            liabilityCategories,
            equityCategories
        );
        
        drawSankeyDiagram();
        addUploadStatus('Financial data extracted and visualized successfully!');
    })
    .catch(error => {
        console.error('Error processing PDF:', error);
        let errorMessage = error.message;
        
        // Provide more user-friendly error messages
        if (errorMessage.includes('NetworkError') || errorMessage.includes('Failed to fetch')) {
            errorMessage = 'Unable to connect to the server. Please check if the server is running.';
        } else if (errorMessage.includes('413')) {
            errorMessage = 'File size is too large. Please choose a smaller file.';
        } else if (errorMessage.includes('415')) {
            errorMessage = 'Invalid file format. Please upload a PDF file.';
        }
        
        addUploadStatus(`Error: ${errorMessage}`);
        useSampleData();
    });
}

// Function to use sample data for the Sankey diagram
function useSampleData() {
    const diagramType = document.getElementById('diagram-type').value;
    
    if (diagramType === 'balance-sheet') {
        // Sample data for Balance Sheet with subsections
        sankeyData.nodes = [
            { name: 'Accounts Payable', value: 2000, category: 'liability', subcategory: 'current' },
            { name: 'Short-term Debt', value: 1000, category: 'liability', subcategory: 'current' },
            { name: 'Long-term Debt', value: 3000, category: 'liability', subcategory: 'non_current' },
            { name: 'Common Stock', value: 5000, category: 'equity' },
            { name: 'Retained Earnings', value: 3000, category: 'equity' },
            { name: 'Total Assets', value: 13000, category: 'total' },
            { name: 'Cash', value: 4000, category: 'asset', subcategory: 'current' },
            { name: 'Accounts Receivable', value: 2000, category: 'asset', subcategory: 'current' },
            { name: 'Property', value: 5000, category: 'asset', subcategory: 'non_current' },
            { name: 'Equipment', value: 2000, category: 'asset', subcategory: 'non_current' }
        ];
        
        sankeyData.links = [
            // Liabilities and Equity to Total Assets
            { source: 0, target: 5, value: 2000 },
            { source: 1, target: 5, value: 1000 },
            { source: 2, target: 5, value: 3000 },
            { source: 3, target: 5, value: 5000 },
            { source: 4, target: 5, value: 3000 },
            // Total Assets to Asset Types
            { source: 5, target: 6, value: 4000 },
            { source: 5, target: 7, value: 2000 },
            { source: 5, target: 8, value: 5000 },
            { source: 5, target: 9, value: 2000 }
        ];
    } else {
        // Sample data for P&L with subsections
        sankeyData.nodes = [
            { name: 'Sales Revenue', value: 5000, category: 'income', subcategory: 'operating' },
            { name: 'Service Revenue', value: 3000, category: 'income', subcategory: 'operating' },
            { name: 'Interest Income', value: 500, category: 'income', subcategory: 'non_operating' },
            { name: 'Total Revenue', value: 8500, category: 'total' },
            { name: 'Costs', value: 6500, category: 'expense' },
            { name: 'Cost of Goods Sold', value: 4000, category: 'expense', subcategory: 'operating' },
            { name: 'Salaries', value: 2000, category: 'expense', subcategory: 'operating' },
            { name: 'Interest Expense', value: 500, category: 'expense', subcategory: 'non_operating' },
            { name: 'Profit', value: 2000, category: 'profit' }
        ];
        
        sankeyData.links = [
            // Revenue streams to Total Revenue
            { source: 0, target: 3, value: 5000 },
            { source: 1, target: 3, value: 3000 },
            { source: 2, target: 3, value: 500 },
            // Total Revenue to Costs and Profit
            { source: 3, target: 4, value: 6500 },
            { source: 3, target: 8, value: 2000 },
            // Costs to Expense Types
            { source: 4, target: 5, value: 4000 },
            { source: 4, target: 6, value: 2000 },
            { source: 4, target: 7, value: 500 }
        ];
    }
    
    drawSankeyDiagram();
}

// Function to prepare Sankey data based on diagram type
function prepareSankeyData(incomeCategories, expenseCategories, transactions, assetCategories = [], liabilityCategories = [], equityCategories = []) {
    const diagramType = document.getElementById('diagram-type').value;
    
    // Clear existing data
    sankeyData.nodes = [];
    sankeyData.links = [];
    
    if (diagramType === 'balance-sheet') {
        // Process Balance Sheet data with subsections
        let nodeIndex = 0;
        const nodeMap = new Map();
        
        // Add liabilities with subsections
        const addLiabilityNodes = (liabilities, subcategory) => {
            liabilities.forEach(liability => {
                nodeMap.set(liability.name, nodeIndex++);
                sankeyData.nodes.push({
                    name: liability.name,
                    value: liability.value,
                    type: 'liability',
                    category: 'liability',
                    subcategory: subcategory
                });
            });
        };
        addLiabilityNodes(liabilityCategories.filter(l => l.subcategory === 'current'), 'current');
        addLiabilityNodes(liabilityCategories.filter(l => l.subcategory === 'non_current'), 'non_current');
        
        // Add equity
        equityCategories.forEach(equity => {
            nodeMap.set(equity.name, nodeIndex++);
            sankeyData.nodes.push({
                name: equity.name,
                value: equity.value,
                type: 'equity',
                category: 'equity'
            });
        });
        
        // Add Total Assets node
        const totalAssets = assetCategories.reduce((sum, asset) => sum + asset.value, 0);
        nodeMap.set('Total Assets', nodeIndex++);
        sankeyData.nodes.push({
            name: 'Total Assets',
            value: totalAssets,
            type: 'total',
            category: 'total'
        });
        
        // Add assets with subsections
        const addAssetNodes = (assets, subcategory) => {
            assets.forEach(asset => {
                nodeMap.set(asset.name, nodeIndex++);
                sankeyData.nodes.push({
                    name: asset.name,
                    value: asset.value,
                    type: 'asset',
                    category: 'asset',
                    subcategory: subcategory
                });
            });
        };
        addAssetNodes(assetCategories.filter(a => a.subcategory === 'current'), 'current');
        addAssetNodes(assetCategories.filter(a => a.subcategory === 'non_current'), 'non_current');
        
        // Create links from liabilities and equity to Total Assets
        liabilityCategories.forEach(liability => {
            sankeyData.links.push({
                source: nodeMap.get(liability.name),
                target: nodeMap.get('Total Assets'),
                value: liability.value
            });
        });
        
        equityCategories.forEach(equity => {
            sankeyData.links.push({
                source: nodeMap.get(equity.name),
                target: nodeMap.get('Total Assets'),
                value: equity.value
            });
        });
        
        // Create links from Total Assets to individual assets
        assetCategories.forEach(asset => {
            sankeyData.links.push({
                source: nodeMap.get('Total Assets'),
                target: nodeMap.get(asset.name),
                value: asset.value
            });
        });
    } else {
        // Process P&L data with subsections
        let nodeIndex = 0;
        const nodeMap = new Map();
        
        // Add revenue streams with subsections
        const addRevenueNodes = (revenues, subcategory) => {
            revenues.forEach(revenue => {
                nodeMap.set(revenue.name, nodeIndex++);
                sankeyData.nodes.push({
                    name: revenue.name,
                    value: revenue.value,
                    type: 'income',
                    category: 'income',
                    subcategory: subcategory
                });
            });
        };
        addRevenueNodes(incomeCategories.filter(r => r.subcategory === 'operating'), 'operating');
        addRevenueNodes(incomeCategories.filter(r => r.subcategory === 'non_operating'), 'non_operating');
        
        // Add Total Revenue node
        const totalRevenue = incomeCategories.reduce((sum, income) => sum + income.value, 0);
        nodeMap.set('Total Revenue', nodeIndex++);
        sankeyData.nodes.push({
            name: 'Total Revenue',
            value: totalRevenue,
            type: 'total',
            category: 'total'
        });
        
        // Add Costs and Profit nodes
        const totalCosts = expenseCategories.reduce((sum, expense) => sum + expense.value, 0);
        const profit = totalRevenue - totalCosts;
        
        nodeMap.set('Costs', nodeIndex++);
        sankeyData.nodes.push({
            name: 'Costs',
            value: totalCosts,
            type: 'expense',
            category: 'expense'
        });
        
        nodeMap.set('Profit', nodeIndex++);
        sankeyData.nodes.push({
            name: 'Profit',
            value: profit > 0 ? profit : 0,
            type: 'profit',
            category: 'profit'
        });
        
        // Add expenses with subsections
        const addExpenseNodes = (expenses, subcategory) => {
            expenses.forEach(expense => {
                nodeMap.set(expense.name, nodeIndex++);
                sankeyData.nodes.push({
                    name: expense.name,
                    value: expense.value,
                    type: 'expense',
                    category: 'expense',
                    subcategory: subcategory
                });
            });
        };
        addExpenseNodes(expenseCategories.filter(e => e.subcategory === 'operating'), 'operating');
        addExpenseNodes(expenseCategories.filter(e => e.subcategory === 'non_operating'), 'non_operating');
        
        // Create links
        incomeCategories.forEach(income => {
            sankeyData.links.push({
                source: nodeMap.get(income.name),
                target: nodeMap.get('Total Revenue'),
                value: income.value
            });
        });
        
        sankeyData.links.push({
            source: nodeMap.get('Total Revenue'),
            target: nodeMap.get('Costs'),
            value: totalCosts
        });
        
        if (profit > 0) {
            sankeyData.links.push({
                source: nodeMap.get('Total Revenue'),
                target: nodeMap.get('Profit'),
                value: profit
            });
        }
        
        expenseCategories.forEach(expense => {
            sankeyData.links.push({
                source: nodeMap.get('Costs'),
                target: nodeMap.get(expense.name),
                value: expense.value
            });
        });
    }
}

// Function to draw the Sankey diagram
function drawSankeyDiagram() {
    // Clear the existing SVG content
    d3.select('#sankey').html('');
    
    // Set up dimensions
    const svg = d3.select('#sankey');
    const width = svg.node().getBoundingClientRect().width;
    const height = svg.node().getBoundingClientRect().height;
    
    // Create the Sankey generator
    const sankey = d3.sankey()
        .nodeWidth(15)
        .nodePadding(10)
        .extent([[20, 20], [width - 20, height - 20]]);
    
    // Generate the Sankey data
    const { nodes, links } = sankey(sankeyData);
    
    // Define color scheme for different node types and subcategories
    const colorMap = {
        'income': {
            'operating': '#66c2a5',
            'non_operating': '#8dd3c7'
        },
        'expense': {
            'operating': '#fc8d62',
            'non_operating': '#ff9e80'
        },
        'asset': {
            'current': '#8da0cb',
            'non_current': '#b3b3ff'
        },
        'liability': {
            'current': '#e78ac3',
            'non_current': '#f4a8d8'
        },
        'equity': '#a6d854',
        'total': '#ffd92f',
        'profit': '#66c2a5'
    };
    
    // Create the link paths
    svg.append('g')
        .selectAll('path')
        .data(links)
        .enter()
        .append('path')
        .attr('d', d3.sankeyLinkHorizontal())
        .attr('stroke-width', d => Math.max(1, d.width))
        .attr('stroke', d => {
            // Color based on source node category and subcategory
            const category = d.source.category;
            const subcategory = d.source.subcategory;
            return colorMap[category][subcategory] || colorMap[category] || '#999';
        })
        .attr('fill', 'none')
        .attr('stroke-opacity', 0.5)
        .append('title')
        .text(d => `${d.source.name} → ${d.target.name}\n${d.value}`);
    
    // Create node groups for better interaction
    const nodeGroup = svg.append('g')
        .selectAll('g')
        .data(nodes)
        .enter()
        .append('g')
        .attr('class', 'node-group')
        .style('cursor', d => d.link ? 'pointer' : 'default')
        .on('click', function(event, d) {
            if (d.link) {
                window.open(d.link, '_blank');
            }
        });
    
    // Add node rectangles
    nodeGroup.append('rect')
        .attr('x', d => d.x0)
        .attr('y', d => d.y0)
        .attr('height', d => d.y1 - d.y0)
        .attr('width', d => d.x1 - d.x0)
        .attr('fill', d => {
            const category = d.category;
            const subcategory = d.subcategory;
            return colorMap[category][subcategory] || colorMap[category] || '#999';
        })
        .attr('stroke', '#000')
        .append('title')
        .text(d => {
            let tooltip = `${d.name}\nValue: ${d.value}`;
            if (d.link) {
                tooltip += '\nClick to view resources';
            }
            return tooltip;
        });
    
    // Add node labels
    nodeGroup.append('text')
        .attr('x', d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
        .attr('y', d => (d.y1 + d.y0) / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', d => d.x0 < width / 2 ? 'start' : 'end')
        .text(d => d.name)
        .style('font-size', '10px')
        .style('font-family', 'Arial, sans-serif')
        .style('pointer-events', 'none');
    
    // Add a small icon to indicate clickable nodes
    nodeGroup.filter(d => d.link)
        .append('text')
        .attr('x', d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
        .attr('y', d => (d.y1 + d.y0) / 2 + 12)
        .attr('dy', '0.35em')
        .attr('text-anchor', d => d.x0 < width / 2 ? 'start' : 'end')
        .text('🔗')
        .style('font-size', '8px')
        .style('pointer-events', 'none');
}

// Function to add a status message to the upload section
function addUploadStatus(message) {
    const uploadSection = document.querySelector('.upload-section');
    
    // Remove any existing status message
    const existingStatus = uploadSection.querySelector('.status-message');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    // Create and add new status message
    const statusDiv = document.createElement('div');
    statusDiv.className = 'status-message';
    statusDiv.textContent = message;
    uploadSection.appendChild(statusDiv);
}

// Function to add a message to the chat
// Function to add a message to the chat
function addChatMessage(sender, content, isAI = false) {
    const chatBody = document.querySelector('.chat-body');
    const messageDiv = document.createElement('div');
    messageDiv.className = isAI ? 'chat-message ai-message' : 'chat-message user-message';
    
    const labelSpan = document.createElement('span');
    labelSpan.className = 'chat-label';
    labelSpan.textContent = sender;
    
    const contentSpan = document.createElement('span');
    contentSpan.className = 'chat-content';
    
    // Use innerHTML for AI messages to support markdown formatting
    if (isAI) {
        // Convert markdown to HTML
        contentSpan.innerHTML = marked.parse(content);
    } else {
        contentSpan.textContent = content;
    }
    
    messageDiv.appendChild(labelSpan);
    messageDiv.appendChild(contentSpan);
    chatBody.appendChild(messageDiv);
    
    // Scroll to the bottom of the chat
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Initialize the page
window.onload = function() {
    // Set up event listeners
    document.getElementById('pdf-upload').addEventListener('change', function() {
        const fileName = this.files[0] ? this.files[0].name : 'No file selected';
        addChatMessage('N', `Selected file: ${fileName}`, false);
    });
    
    // Initialize with sample data
    useSampleData();
    
    // Resize handler for the Sankey diagram
    window.addEventListener('resize', function() {
        drawSankeyDiagram();
    });
    
    // Add event listener for diagram type change
    document.getElementById('diagram-type').addEventListener('change', function() {
        useSampleData();
    });
};

function sendMessage() {
    const inputField = document.getElementById('chat-input-field');
    const message = inputField.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage('User', message);
    
    // Clear input field
    inputField.value = '';
    
    // Process the message and generate AI response
    processUserMessage(message);
}

function processUserMessage(message) {
    // Get the financial data from the last processed PDF
    const financialData = window.lastProcessedData;
    
    if (!financialData) {
        addChatMessage('AI', 'Please upload a financial document first to analyze metrics.', true);
        return;
    }
    
    // Show loading message
    addChatMessage('AI', 'Analyzing your question...', true);
    
    // Send the message and financial data to the backend API
    // Get the base URL dynamically (works both locally and when deployed)
    const baseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:5000' 
        : window.location.origin;
        
    fetch(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            financial_data: financialData
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Server error: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        // Remove the loading message
        const chatBody = document.querySelector('.chat-body');
        chatBody.removeChild(chatBody.lastChild);
        
        // Add the AI response to the chat
        addChatMessage('AI', data.response, true);
    })
    .catch(error => {
        console.error('Error processing message:', error);
        
        // Remove the loading message
        const chatBody = document.querySelector('.chat-body');
        chatBody.removeChild(chatBody.lastChild);
        
        // Add error message to chat
        addChatMessage('AI', `Sorry, I encountered an error: ${error.message}`, true);
    });
}

function calculateFinancialMetrics(data) {
    const metrics = {
        wacc: 0,
        costOfDebt: 0,
        taxRate: 0,
        debtToEquity: 0,
        profit: 0
    };
    
    // Calculate WACC
    const totalDebt = data.balance_sheet.liabilities.current.reduce((sum, item) => sum + item.value, 0) +
                      data.balance_sheet.liabilities.non_current.reduce((sum, item) => sum + item.value, 0);
    const totalEquity = data.balance_sheet.equity.reduce((sum, item) => sum + item.value, 0);
    const totalCapital = totalDebt + totalEquity;
    
    // Assume cost of equity is 10% and cost of debt is 5% (these should be calculated based on actual data)
    const costOfEquity = 0.10;
    metrics.costOfDebt = 0.05;
    
    // Calculate tax rate based on income and profit
    const totalRevenue = data.income_statement.revenue.operating.reduce((sum, item) => sum + item.value, 0) +
                        data.income_statement.revenue.non_operating.reduce((sum, item) => sum + item.value, 0);
    const totalExpenses = data.income_statement.expenses.operating.reduce((sum, item) => sum + item.value, 0) +
                         data.income_statement.expenses.non_operating.reduce((sum, item) => sum + item.value, 0);
    metrics.profit = totalRevenue - totalExpenses;
    
    // Assume standard corporate tax rate of 30%
    metrics.taxRate = 0.30;
    
    // Calculate WACC
    metrics.wacc = (totalEquity / totalCapital) * costOfEquity +
                   (totalDebt / totalCapital) * metrics.costOfDebt * (1 - metrics.taxRate);
    
    // Calculate Debt to Equity ratio
    metrics.debtToEquity = totalDebt / totalEquity;
    
    return metrics;
}

function generateAIResponse(message, metrics) {
    const query = message.toLowerCase();
    
    if (query.includes('wacc')) {
        return `The Weighted Average Cost of Capital (WACC) is ${(metrics.wacc * 100).toFixed(2)}%. This represents the average rate that the company is expected to pay to finance its assets.`;
    }
    else if (query.includes('debt') && query.includes('equity')) {
        return `The Debt to Equity ratio is ${metrics.debtToEquity.toFixed(2)}. This indicates the proportion of debt and equity the company is using to finance its assets.`;
    }
    else if (query.includes('tax')) {
        return `The effective tax rate is ${(metrics.taxRate * 100).toFixed(2)}%. This represents the percentage of profit that goes to tax payments.`;
    }
    else if (query.includes('profit')) {
        return `The current profit is ${metrics.profit.toFixed(2)}. This is calculated as the difference between total revenue and total expenses.`;
    }
    else if (query.includes('cost of debt')) {
        return `The cost of debt is ${(metrics.costOfDebt * 100).toFixed(2)}%. This represents the effective interest rate the company pays on its borrowings.`;
    }
    else {
        return `I can provide information about various financial metrics including WACC, debt to equity ratio, tax rate, profit, and cost of debt. What would you like to know about?`;
    }
}

// Modify processPDF function to store the last processed data
const originalProcessPDF = window.processPDF;
window.processPDF = function() {
    originalProcessPDF.apply(this, arguments);
    // Store the processed data for chat analysis
    window.lastProcessedData = financialData;
};