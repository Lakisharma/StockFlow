/* global window, document, alert, authService, apiService, productService, inventoryService, purchaseService, salesService, transferService, accountingService, reportService, ocrService, aiAssistantService, notificationService, settingsService, backupService */
/**
 * StockFlow AI Desktop Application Renderer Logic
 * Binds UI elements, Django REST API calls, barcode scanner events, and navigation.
 */
document.addEventListener('DOMContentLoaded', () => {

  // Dynamically update connection endpoint display
  const connectionUrlEl = document.getElementById('connectionUrl');
  if (connectionUrlEl && typeof CONFIG !== 'undefined') {
    connectionUrlEl.textContent = CONFIG.API_BASE_URL;
  }

  // DOM Window Controls
  const btnWindowMinimize = document.getElementById('btnWindowMinimize');
  const btnWindowMaximize = document.getElementById('btnWindowMaximize');
  const btnWindowClose = document.getElementById('btnWindowClose');

  // DOM Authentication
  const loginScreen = document.getElementById('loginScreen');
  const appContainer = document.getElementById('appContainer');
  const desktopLoginForm = document.getElementById('desktopLoginForm');
  const inputUsername = document.getElementById('inputUsername');
  const inputPassword = document.getElementById('inputPassword');
  const loginAlert = document.getElementById('loginAlert');
  const btnDesktopLogout = document.getElementById('btnDesktopLogout');

  // DOM Navigation
  const navItems = document.querySelectorAll('.nav-item');
  const viewPanels = document.querySelectorAll('.view-panel');

  // Dashboard Metrics
  const kpiProducts = document.getElementById('kpiProducts');
  const kpiPurchases = document.getElementById('kpiPurchases');
  const kpiSales = document.getElementById('kpiSales');
  const kpiHealth = document.getElementById('kpiHealth');

  // Notification Elements
  const headerUnreadBadge = document.getElementById('headerUnreadBadge');
  const notificationsMainTableBody = document.getElementById('notificationsMainTableBody');

  // View Data Bodies
  const productsTableBody = document.getElementById('productsTableBody');
  const inventoryTableBody = document.getElementById('inventoryTableBody');
  const transfersTableBody = document.getElementById('transfersTableBody');
  const purchasesTableBody = document.getElementById('purchasesTableBody');
  const salesTableBody = document.getElementById('salesTableBody');
  const expensesTableBody = document.getElementById('expensesTableBody');
  const settingsUsersTableBody = document.getElementById('settingsUsersTableBody');
  const backupsHistoryTableBody = document.getElementById('backupsHistoryTableBody');

  // Reports KPI Elements
  const reportKpiRevenue = document.getElementById('reportKpiRevenue');
  const reportKpiPurchases = document.getElementById('reportKpiPurchases');
  const reportKpiStockValue = document.getElementById('reportKpiStockValue');
  const reportKpiLowStock = document.getElementById('reportKpiLowStock');

  // 1. Electron IPC Window Controls Bridge
  if (window.electronAPI) {
    if (btnWindowMinimize) btnWindowMinimize.addEventListener('click', () => window.electronAPI.minimizeWindow());
    if (btnWindowMaximize) btnWindowMaximize.addEventListener('click', () => window.electronAPI.maximizeWindow());
    if (btnWindowClose) btnWindowClose.addEventListener('click', () => window.electronAPI.closeWindow());
  }

  // 2. Desktop Login Handling with Double-Submission Protection
  if (desktopLoginForm) {
    desktopLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      loginAlert.style.display = 'none';

      const submitBtn = desktopLoginForm.querySelector('button[type="submit"]');
      if (submitBtn) submitBtn.disabled = true;

      const userVal = inputUsername.value.trim();
      const passVal = inputPassword.value.trim();

      try {
        const result = await authService.login(userVal, passVal);
        if (result.success) {
          loginScreen.style.display = 'none';
          appContainer.style.display = 'flex';
          loadDashboardMetrics();
          loadNotificationsData();
        }
      } catch (err) {
        loginAlert.textContent = err.message || "Login failed. Check server connection.";
        loginAlert.style.display = 'block';
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // 3. Desktop Logout Handling
  if (btnDesktopLogout) {
    btnDesktopLogout.addEventListener('click', () => {
      authService.logout();
      appContainer.style.display = 'none';
      loginScreen.style.display = 'flex';
    });
  }

  // 4. Sidebar Navigation View Switching
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = item.getAttribute('data-view');
      switchDesktopView(targetView, item.innerText.trim());
    });
  });

  function switchDesktopView(targetView, title = '') {
    navItems.forEach(n => n.classList.remove('active'));
    const activeNav = document.querySelector(`.nav-item[data-view="${targetView}"]`);
    if (activeNav) activeNav.classList.add('active');

    viewPanels.forEach(p => p.classList.remove('active'));

    const panel = document.getElementById(`view${targetView.charAt(0).toUpperCase() + targetView.slice(1)}`);
    if (panel) {
      panel.classList.add('active');
      if (targetView === 'products') loadProductsTable();
      else if (targetView === 'inventory') loadInventoryTable();
      else if (targetView === 'transfers') loadTransfersTable();
      else if (targetView === 'purchases') loadPurchasesTable();
      else if (targetView === 'sales') loadSalesTable();
      else if (targetView === 'accounting') loadExpensesTable();
      else if (targetView === 'reports') loadReportsData();
      else if (targetView === 'notifications') loadNotificationsData();
      else if (targetView === 'settings') loadSettingsData();
      else if (targetView === 'backups') loadBackupsData();
    } else {
      const genericView = document.getElementById('viewGeneric');
      document.getElementById('genericViewTitle').textContent = title || targetView;
      document.getElementById('genericViewContent').innerHTML = `
        <div class="kpi-card" style="margin-top:20px;">
          <p>Connected to Django REST API endpoint <code>/api/${targetView}/</code></p>
        </div>
      `;
      genericView.classList.add('active');
    }
  }

  // 5. Load Dashboard Metrics
  async function loadDashboardMetrics() {
    try {
      const isHealthy = await apiService.checkHealth();
      kpiHealth.textContent = isHealthy ? "Healthy" : "Offline";
      kpiHealth.style.color = isHealthy ? "#10b981" : "#ef4444";

      const prodRes = await productService.getProducts();
      if (Array.isArray(prodRes)) kpiProducts.textContent = prodRes.length;

      const poRes = await purchaseService.getPurchaseOrders();
      if (Array.isArray(poRes)) kpiPurchases.textContent = poRes.length;

      const salesRes = await salesService.getSalesDispatches();
      if (Array.isArray(salesRes)) kpiSales.textContent = salesRes.length;
    } catch (err) {
      console.warn("[Desktop App] Error loading dashboard metrics:", err);
    }
  }

  // Data Loading Helpers
  async function loadProductsTable() {
    if (!productsTableBody) return;
    productsTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Loading products...</td></tr>`;
    const list = await productService.getProducts();
    if (!Array.isArray(list) || list.length === 0) {
      productsTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No products found.</td></tr>`;
      return;
    }
    let rows = '';
    list.forEach(p => {
      rows += `
        <tr>
          <td>#${p.id}</td>
          <td><strong>${p.name}</strong></td>
          <td><code>${p.sku}</code></td>
          <td><code>${p.barcode || '--'}</code></td>
          <td>$${parseFloat(p.selling_price || 0).toFixed(2)}</td>
          <td>${p.current_stock || 0}</td>
          <td><span class="badge badge-success">Active</span></td>
          <td><button class="btn-secondary btn-sm">Edit</button></td>
        </tr>
      `;
    });
    productsTableBody.innerHTML = rows;
  }

  async function loadInventoryTable() {
    if (!inventoryTableBody) return;
    inventoryTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Loading inventory balances...</td></tr>`;
    const list = await inventoryService.getWarehouseStock();
    if (!Array.isArray(list) || list.length === 0) {
      inventoryTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No stock balances found.</td></tr>`;
      return;
    }
    let rows = '';
    list.forEach(i => {
      rows += `
        <tr>
          <td><strong>${i.product_name || i.product || 'Product'}</strong></td>
          <td>${i.warehouse_name || i.warehouse || 'Main Warehouse'}</td>
          <td><strong>${i.quantity || 0}</strong></td>
          <td>${i.batch_number || '--'}</td>
          <td><span class="badge badge-success">Available</span></td>
          <td>${i.updated_at ? i.updated_at.slice(0,10) : 'Today'}</td>
        </tr>
      `;
    });
    inventoryTableBody.innerHTML = rows;
  }

  async function loadTransfersTable() {
    if (!transfersTableBody) return;
    transfersTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Loading stock transfers...</td></tr>`;
    const list = await transferService.getStockTransfers();
    if (!Array.isArray(list) || list.length === 0) {
      transfersTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No stock transfers found.</td></tr>`;
      return;
    }
    let rows = '';
    list.forEach(t => {
      rows += `
        <tr>
          <td>#${t.id}</td>
          <td>${t.from_warehouse_name || t.from_warehouse}</td>
          <td>${t.to_warehouse_name || t.to_warehouse}</td>
          <td>${t.quantity || 0}</td>
          <td><span class="badge badge-info">${t.status || 'Received'}</span></td>
          <td>${t.transfer_date || '--'}</td>
        </tr>
      `;
    });
    transfersTableBody.innerHTML = rows;
  }

  async function loadPurchasesTable() {
    if (!purchasesTableBody) return;
    purchasesTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Loading purchase orders...</td></tr>`;
    const list = await purchaseService.getPurchaseOrders();
    if (!Array.isArray(list) || list.length === 0) {
      purchasesTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No purchase orders found.</td></tr>`;
      return;
    }
    let rows = '';
    list.forEach(p => {
      rows += `
        <tr>
          <td><strong>${p.po_number || `#${p.id}`}</strong></td>
          <td>${p.supplier_name || 'Supplier'}</td>
          <td>${p.warehouse_name || 'Main Warehouse'}</td>
          <td>$${parseFloat(p.total_amount || 0).toFixed(2)}</td>
          <td><span class="badge badge-success">${p.status || 'Completed'}</span></td>
          <td>${p.order_date || '--'}</td>
        </tr>
      `;
    });
    purchasesTableBody.innerHTML = rows;
  }

  async function loadSalesTable() {
    if (!salesTableBody) return;
    salesTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Loading sales dispatches...</td></tr>`;
    const list = await salesService.getSalesDispatches();
    if (!Array.isArray(list) || list.length === 0) {
      salesTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No sales dispatches found.</td></tr>`;
      return;
    }
    let rows = '';
    list.forEach(s => {
      rows += `
        <tr>
          <td><strong>${s.dispatch_number || s.invoice_number || `#${s.id}`}</strong></td>
          <td>${s.customer_name || 'Walk-in Customer'}</td>
          <td>${s.warehouse_name || 'Main Warehouse'}</td>
          <td>$${parseFloat(s.total_amount || 0).toFixed(2)}</td>
          <td><span class="badge badge-success">Paid</span></td>
          <td><span class="badge badge-info">Dispatched</span></td>
          <td>${s.dispatch_date || '--'}</td>
        </tr>
      `;
    });
    salesTableBody.innerHTML = rows;
  }

  async function loadExpensesTable() {
    if (!expensesTableBody) return;
    expensesTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Loading expenses...</td></tr>`;
    const list = await accountingService.getExpenses();
    if (!Array.isArray(list) || list.length === 0) {
      expensesTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No expenses recorded.</td></tr>`;
      return;
    }
    let rows = '';
    list.forEach(e => {
      rows += `
        <tr>
          <td>#${e.id}</td>
          <td>${e.category_name || 'Expense'}</td>
          <td>${e.payment_method || 'cash'}</td>
          <td>$${parseFloat(e.amount || 0).toFixed(2)}</td>
          <td><span class="badge badge-success">Approved</span></td>
          <td>${e.expense_date || '--'}</td>
        </tr>
      `;
    });
    expensesTableBody.innerHTML = rows;
  }

  const reportsComparisonTableBody = document.getElementById('reportsComparisonTableBody');

  async function loadReportsData() {
    try {
      const data = await reportService.getDashboardMetrics();
      if (reportKpiRevenue) reportKpiRevenue.textContent = `₹${parseFloat(data.total_sales || 0).toFixed(2)}`;
      if (reportKpiPurchases) reportKpiPurchases.textContent = `₹${parseFloat(data.total_purchases || data.total_purchase_amount || 0).toFixed(2)}`;
      if (reportKpiStockValue) reportKpiStockValue.textContent = `₹${parseFloat(data.inventory_value || data.total_inventory_value || 0).toFixed(2)}`;
      if (reportKpiLowStock) reportKpiLowStock.textContent = data.low_stock_count || 0;

      if (reportsComparisonTableBody) {
        const whList = await reportService.getWarehouseComparison();
        if (!Array.isArray(whList) || whList.length === 0) {
          reportsComparisonTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding:24px;">No warehouse comparison metrics yet (0 warehouses registered in production).</td></tr>`;
        } else {
          let rows = '';
          whList.forEach(w => {
            rows += `
              <tr>
                <td><strong>${w.name || w.warehouse_name || 'Warehouse'}</strong></td>
                <td><code>${w.code || '--'}</code></td>
                <td>${w.total_products || w.product_count || 0}</td>
                <td><strong>${w.physical_stock || w.total_stock || 0}</strong></td>
                <td><span class="badge badge-success">${w.status || 'Active'}</span></td>
              </tr>
            `;
          });
          reportsComparisonTableBody.innerHTML = rows;
        }
      }
    } catch (err) {
      console.warn("[Desktop App] Error loading reports:", err);
      if (reportsComparisonTableBody) {
        reportsComparisonTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding:24px;">No warehouse data available.</td></tr>`;
      }
    }
  }

  async function loadNotificationsData() {
    const list = await notificationService.getNotifications();
    const unreadCount = list.filter(n => !n.is_read).length;
    if (headerUnreadBadge) {
      headerUnreadBadge.textContent = unreadCount;
      headerUnreadBadge.style.display = unreadCount > 0 ? 'inline-block' : 'none';
    }
    if (notificationsMainTableBody) {
      if (list.length === 0) {
        notificationsMainTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No notifications found.</td></tr>`;
      } else {
        let rows = '';
        list.forEach(n => {
          rows += `
            <tr>
              <td><span class="badge badge-warning">${n.priority || 'normal'}</span></td>
              <td><code>${n.notification_type || 'system'}</code></td>
              <td><strong>${n.title}</strong><div class="text-muted" style="font-size:12px;">${n.message}</div></td>
              <td>${n.is_read ? '<span class="badge badge-secondary">Read</span>' : '<span class="badge badge-warning">Unread</span>'}</td>
              <td>${n.created_at ? n.created_at.slice(0,10) : '--'}</td>
              <td>${!n.is_read ? `<button class="btn-secondary btn-sm" onclick="markNotificationRead(${n.id})">Mark Read</button>` : 'Completed'}</td>
            </tr>
          `;
        });
        notificationsMainTableBody.innerHTML = rows;
      }
    }
  }

  async function loadSettingsData() {
    if (!settingsUsersTableBody) return;
    const users = await settingsService.getUsersList();
    if (!Array.isArray(users) || users.length === 0) {
      settingsUsersTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No users found.</td></tr>`;
      return;
    }
    let rows = '';
    users.forEach(u => {
      rows += `
        <tr>
          <td>#${u.id}</td>
          <td><strong>${u.username}</strong></td>
          <td>${u.email || '--'}</td>
          <td><span class="badge badge-info">${u.role_name || 'Staff'}</span></td>
          <td><span class="badge badge-success">Active</span></td>
        </tr>
      `;
    });
    settingsUsersTableBody.innerHTML = rows;
  }

  async function loadBackupsData() {
    if (!backupsHistoryTableBody) return;
    const list = await backupService.getBackupHistory();
    if (!Array.isArray(list) || list.length === 0) {
      backupsHistoryTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No database backups found.</td></tr>`;
      return;
    }
    let rows = '';
    list.forEach(b => {
      rows += `
        <tr>
          <td>#${b.id}</td>
          <td><strong>${b.filename || b.name || `backup_${b.id}.zip`}</strong></td>
          <td>${b.file_size || '1.2 MB'}</td>
          <td><span class="badge badge-success">Completed</span></td>
          <td>${b.created_at ? b.created_at.slice(0,10) : '--'}</td>
          <td><button class="btn-secondary btn-sm">Verified</button></td>
        </tr>
      `;
    });
    backupsHistoryTableBody.innerHTML = rows;
  }

  // 6. Product Creation Modal Handlers
  const btnOpenCreateProductModal = document.getElementById('btnOpenCreateProductModal');
  const modalCreateProduct = document.getElementById('modalCreateProduct');
  const btnCloseProductModal = document.getElementById('btnCloseProductModal');
  const btnCancelProductModal = document.getElementById('btnCancelProductModal');
  const formCreateProduct = document.getElementById('formCreateProduct');

  if (btnOpenCreateProductModal && modalCreateProduct) {
    btnOpenCreateProductModal.addEventListener('click', () => {
      modalCreateProduct.style.display = 'flex';
    });
  }

  if (btnCloseProductModal && modalCreateProduct) {
    btnCloseProductModal.addEventListener('click', () => {
      modalCreateProduct.style.display = 'none';
    });
  }

  if (btnCancelProductModal && modalCreateProduct) {
    btnCancelProductModal.addEventListener('click', () => {
      modalCreateProduct.style.display = 'none';
    });
  }

  if (formCreateProduct) {
    formCreateProduct.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('prodName').value.trim();
      const sku = document.getElementById('prodSku').value.trim();
      const barcode = document.getElementById('prodBarcode').value.trim();
      const selling_price = document.getElementById('prodPrice').value.trim();
      const reorder_level = document.getElementById('prodReorderLevel').value.trim();

      const submitBtn = formCreateProduct.querySelector('button[type="submit"]');
      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Saving...'; }

      const res = await productService.createProduct({
        name, sku, barcode, selling_price, reorder_level
      });

      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Save Product to Server'; }

      if (res.success) {
        alert(`✅ Product "${name}" created successfully on the server!`);
        formCreateProduct.reset();
        modalCreateProduct.style.display = 'none';
        loadProductsTable();
        loadDashboardMetrics();
      } else {
        alert(`❌ Error creating product: ${res.error || 'Check fields or server connection'}`);
      }
    });
  }

  // 7. Change Password Modal Handlers
  const btnOpenChangePasswordModal = document.getElementById('btnOpenChangePasswordModal');
  const modalChangePassword = document.getElementById('modalChangePassword');
  const btnClosePasswordModal = document.getElementById('btnClosePasswordModal');
  const btnCancelPasswordModal = document.getElementById('btnCancelPasswordModal');
  const formChangePassword = document.getElementById('formChangePassword');

  if (btnOpenChangePasswordModal && modalChangePassword) {
    btnOpenChangePasswordModal.addEventListener('click', () => {
      modalChangePassword.style.display = 'flex';
    });
  }

  if (btnClosePasswordModal && modalChangePassword) {
    btnClosePasswordModal.addEventListener('click', () => {
      modalChangePassword.style.display = 'none';
    });
  }

  if (btnCancelPasswordModal && modalChangePassword) {
    btnCancelPasswordModal.addEventListener('click', () => {
      modalChangePassword.style.display = 'none';
    });
  }

  if (formChangePassword) {
    formChangePassword.addEventListener('submit', async (e) => {
      e.preventDefault();
      const currentPass = document.getElementById('inputCurrentPass').value;
      const newPass = document.getElementById('inputNewPass').value;
      const confirmPass = document.getElementById('inputConfirmPass').value;

      if (newPass !== confirmPass) {
        alert("❌ New password and confirmation do not match.");
        return;
      }

      if (newPass.length < 6) {
        alert("❌ New password must be at least 6 characters long.");
        return;
      }

      const submitBtn = formChangePassword.querySelector('button[type="submit"]');
      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Updating...'; }

      const res = await authService.changePassword(currentPass, newPass);

      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Update Password'; }

      if (res.success) {
        alert("✅ Password updated successfully! Please use your new password next time you sign in.");
        formChangePassword.reset();
        modalChangePassword.style.display = 'none';
      } else {
        alert(`❌ Error updating password: ${res.error || 'Current password might be incorrect'}`);
      }
    });
  }

  // 8. AI Smart Assistant Chat Handlers
  const formAiChatInput = document.getElementById('formAiChatInput');
  const inputAiQuery = document.getElementById('inputAiQuery');
  const aiChatHistory = document.getElementById('aiChatHistory');

  function appendChatMessage(sender, text) {
    if (!aiChatHistory) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;
    const iconName = sender === 'assistant' ? 'smart_toy' : 'person';
    const formattedText = text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
    msgDiv.innerHTML = `
      <span class="material-icons-round icon">${iconName}</span>
      <div class="message-content">
        <p>${formattedText}</p>
      </div>
    `;
    aiChatHistory.appendChild(msgDiv);
    aiChatHistory.scrollTop = aiChatHistory.scrollHeight;
  }

  if (formAiChatInput && inputAiQuery) {
    formAiChatInput.addEventListener('submit', async (e) => {
      e.preventDefault();
      const query = inputAiQuery.value.trim();
      if (!query) return;

      appendChatMessage('user', query);
      inputAiQuery.value = '';

      // Typing indicator
      appendChatMessage('assistant', 'Thinking...');
      const thinkingEl = aiChatHistory.lastElementChild;

      const result = await aiAssistantService.parseAndExecuteQuery(query);
      if (thinkingEl && thinkingEl.parentNode) {
        thinkingEl.parentNode.removeChild(thinkingEl);
      }

      appendChatMessage('assistant', result.response_text || 'I could not process your query.');
    });
  }

  window.sendAiChip = function(queryText) {
    if (inputAiQuery && formAiChatInput) {
      inputAiQuery.value = queryText;
      formAiChatInput.dispatchEvent(new Event('submit'));
    }
  };

  // 9. Report Export & Print Actions
  const btnExportSalesCsv = document.getElementById('btnExportSalesCsv');
  const btnExportInventoryCsv = document.getElementById('btnExportInventoryCsv');
  const btnPrintReports = document.getElementById('btnPrintReports');

  if (btnExportSalesCsv) {
    btnExportSalesCsv.addEventListener('click', async () => {
      const list = await salesService.getSalesDispatches();
      let csv = "Invoice,Customer,Warehouse,Amount,Status,Date\n";
      list.forEach(s => {
        csv += `"${s.invoice_number || s.id}","${s.customer_name || 'Customer'}","${s.warehouse_name || 'Warehouse'}","${s.total_amount || 0}","${s.payment_status || 'Paid'}","${s.dispatch_date || ''}"\n`;
      });
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sales_report_${new Date().toISOString().slice(0,10)}.csv`;
      a.click();
    });
  }

  if (btnExportInventoryCsv) {
    btnExportInventoryCsv.addEventListener('click', async () => {
      const list = await inventoryService.getWarehouseStock();
      let csv = "Product,Warehouse,Quantity,Batch,Status\n";
      list.forEach(i => {
        csv += `"${i.product_name || i.product}","${i.warehouse_name || i.warehouse}","${i.quantity || 0}","${i.batch_number || ''}","Available"\n`;
      });
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `inventory_report_${new Date().toISOString().slice(0,10)}.csv`;
      a.click();
    });
  }

  if (btnPrintReports) {
    btnPrintReports.addEventListener('click', () => {
      window.print();
    });
  }

});
