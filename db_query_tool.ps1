# Database Query Tool - PowerShell GUI
# Double-click to run, or right-click -> Run with PowerShell

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Database Query Tool"
$form.Size = New-Object System.Drawing.Size(1000, 750)
$form.StartPosition = "CenterScreen"
$form.Font = New-Object System.Drawing.Font("Segoe UI", 9)

# Connection Panel
$connPanel = New-Object System.Windows.Forms.GroupBox
$connPanel.Text = "Connection Settings"
$connPanel.Location = New-Object System.Drawing.Point(10, 10)
$connPanel.Size = New-Object System.Drawing.Size(960, 80)

# Server
$lblServer = New-Object System.Windows.Forms.Label
$lblServer.Text = "Server:"
$lblServer.Location = New-Object System.Drawing.Point(10, 25)
$lblServer.Size = New-Object System.Drawing.Size(50, 20)
$connPanel.Controls.Add($lblServer)

$txtServer = New-Object System.Windows.Forms.TextBox
$txtServer.Text = "p-budg-w-db19"
$txtServer.Location = New-Object System.Drawing.Point(65, 22)
$txtServer.Size = New-Object System.Drawing.Size(180, 20)
$connPanel.Controls.Add($txtServer)

# Port
$lblPort = New-Object System.Windows.Forms.Label
$lblPort.Text = "Port:"
$lblPort.Location = New-Object System.Drawing.Point(255, 25)
$lblPort.Size = New-Object System.Drawing.Size(35, 20)
$connPanel.Controls.Add($lblPort)

$txtPort = New-Object System.Windows.Forms.TextBox
$txtPort.Text = "1433"
$txtPort.Location = New-Object System.Drawing.Point(295, 22)
$txtPort.Size = New-Object System.Drawing.Size(60, 20)
$connPanel.Controls.Add($txtPort)

# Database
$lblDatabase = New-Object System.Windows.Forms.Label
$lblDatabase.Text = "Database:"
$lblDatabase.Location = New-Object System.Drawing.Point(365, 25)
$lblDatabase.Size = New-Object System.Drawing.Size(60, 20)
$connPanel.Controls.Add($lblDatabase)

$txtDatabase = New-Object System.Windows.Forms.TextBox
$txtDatabase.Text = "budg"
$txtDatabase.Location = New-Object System.Drawing.Point(430, 22)
$txtDatabase.Size = New-Object System.Drawing.Size(120, 20)
$connPanel.Controls.Add($txtDatabase)

# Auth Type
$lblAuth = New-Object System.Windows.Forms.Label
$lblAuth.Text = "Auth:"
$lblAuth.Location = New-Object System.Drawing.Point(560, 25)
$lblAuth.Size = New-Object System.Drawing.Size(35, 20)
$connPanel.Controls.Add($lblAuth)

$cboAuth = New-Object System.Windows.Forms.ComboBox
$cboAuth.Items.AddRange(@("Windows Authentication", "SQL Server Authentication"))
$cboAuth.SelectedIndex = 0
$cboAuth.Location = New-Object System.Drawing.Point(600, 22)
$cboAuth.Size = New-Object System.Drawing.Size(170, 20)
$cboAuth.DropDownStyle = "DropDownList"
$connPanel.Controls.Add($cboAuth)

# Test Connection Button
$btnTest = New-Object System.Windows.Forms.Button
$btnTest.Text = "Test Connection"
$btnTest.Location = New-Object System.Drawing.Point(785, 20)
$btnTest.Size = New-Object System.Drawing.Size(110, 28)
$btnTest.BackColor = [System.Drawing.Color]::FromArgb(40, 167, 69)
$btnTest.ForeColor = [System.Drawing.Color]::White
$connPanel.Controls.Add($btnTest)

# SQL Auth fields (hidden by default)
$lblUser = New-Object System.Windows.Forms.Label
$lblUser.Text = "Username:"
$lblUser.Location = New-Object System.Drawing.Point(10, 52)
$lblUser.Size = New-Object System.Drawing.Size(60, 20)
$lblUser.Visible = $false
$connPanel.Controls.Add($lblUser)

$txtUser = New-Object System.Windows.Forms.TextBox
$txtUser.Location = New-Object System.Drawing.Point(75, 50)
$txtUser.Size = New-Object System.Drawing.Size(150, 20)
$txtUser.Visible = $false
$connPanel.Controls.Add($txtUser)

$lblPass = New-Object System.Windows.Forms.Label
$lblPass.Text = "Password:"
$lblPass.Location = New-Object System.Drawing.Point(235, 52)
$lblPass.Size = New-Object System.Drawing.Size(60, 20)
$lblPass.Visible = $false
$connPanel.Controls.Add($lblPass)

$txtPass = New-Object System.Windows.Forms.TextBox
$txtPass.Location = New-Object System.Drawing.Point(300, 50)
$txtPass.Size = New-Object System.Drawing.Size(150, 20)
$txtPass.UseSystemPasswordChar = $true
$txtPass.Visible = $false
$connPanel.Controls.Add($txtPass)

$form.Controls.Add($connPanel)

# Toggle SQL auth fields
$cboAuth.Add_SelectedIndexChanged({
    $showSql = $cboAuth.SelectedIndex -eq 1
    $lblUser.Visible = $showSql
    $txtUser.Visible = $showSql
    $lblPass.Visible = $showSql
    $txtPass.Visible = $showSql
})

# Query Panel
$queryPanel = New-Object System.Windows.Forms.GroupBox
$queryPanel.Text = "SQL Query"
$queryPanel.Location = New-Object System.Drawing.Point(10, 95)
$queryPanel.Size = New-Object System.Drawing.Size(960, 180)

$txtQuery = New-Object System.Windows.Forms.TextBox
$txtQuery.Multiline = $true
$txtQuery.ScrollBars = "Vertical"
$txtQuery.Font = New-Object System.Drawing.Font("Consolas", 10)
$txtQuery.Location = New-Object System.Drawing.Point(10, 20)
$txtQuery.Size = New-Object System.Drawing.Size(940, 110)
$txtQuery.Text = @"
SELECT SUM(m.NetAmount) AS TotalNetAmount
FROM eis.RD_REPORTING_2026 m
WHERE m.BudgFy = '2026'
AND m.fundingCode = '01002627DB'
"@
$queryPanel.Controls.Add($txtQuery)

# Buttons
$btnExecute = New-Object System.Windows.Forms.Button
$btnExecute.Text = "Execute Query"
$btnExecute.Location = New-Object System.Drawing.Point(10, 140)
$btnExecute.Size = New-Object System.Drawing.Size(120, 30)
$btnExecute.BackColor = [System.Drawing.Color]::FromArgb(0, 120, 212)
$btnExecute.ForeColor = [System.Drawing.Color]::White
$queryPanel.Controls.Add($btnExecute)

$btnClear = New-Object System.Windows.Forms.Button
$btnClear.Text = "Clear"
$btnClear.Location = New-Object System.Drawing.Point(140, 140)
$btnClear.Size = New-Object System.Drawing.Size(80, 30)
$queryPanel.Controls.Add($btnClear)

$btnExport = New-Object System.Windows.Forms.Button
$btnExport.Text = "Export to CSV"
$btnExport.Location = New-Object System.Drawing.Point(230, 140)
$btnExport.Size = New-Object System.Drawing.Size(100, 30)
$queryPanel.Controls.Add($btnExport)

$form.Controls.Add($queryPanel)

# Status Label
$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Location = New-Object System.Drawing.Point(10, 280)
$lblStatus.Size = New-Object System.Drawing.Size(960, 25)
$lblStatus.Text = "Ready"
$form.Controls.Add($lblStatus)

# Results Grid
$dataGrid = New-Object System.Windows.Forms.DataGridView
$dataGrid.Location = New-Object System.Drawing.Point(10, 310)
$dataGrid.Size = New-Object System.Drawing.Size(960, 390)
$dataGrid.AllowUserToAddRows = $false
$dataGrid.AllowUserToDeleteRows = $false
$dataGrid.ReadOnly = $true
$dataGrid.AutoSizeColumnsMode = "AllCells"
$dataGrid.SelectionMode = "FullRowSelect"
$dataGrid.BackgroundColor = [System.Drawing.Color]::White
$form.Controls.Add($dataGrid)

# Store results for export
$script:lastResults = $null

# Function to get connection string
function Get-ConnectionString {
    $server = $txtServer.Text
    $port = $txtPort.Text
    $database = $txtDatabase.Text

    if ($cboAuth.SelectedIndex -eq 0) {
        # Windows Authentication
        return "Server=$server,$port;Database=$database;Integrated Security=True;TrustServerCertificate=True;"
    } else {
        # SQL Server Authentication
        $user = $txtUser.Text
        $pass = $txtPass.Text
        return "Server=$server,$port;Database=$database;User Id=$user;Password=$pass;TrustServerCertificate=True;"
    }
}

# Test Connection
$btnTest.Add_Click({
    try {
        $lblStatus.Text = "Testing connection..."
        $lblStatus.ForeColor = [System.Drawing.Color]::Blue
        $form.Refresh()

        $connString = Get-ConnectionString
        $conn = New-Object System.Data.SqlClient.SqlConnection($connString)
        $conn.Open()
        $conn.Close()

        $lblStatus.Text = "Connection successful!"
        $lblStatus.ForeColor = [System.Drawing.Color]::Green
    }
    catch {
        $lblStatus.Text = "Connection failed: $($_.Exception.Message)"
        $lblStatus.ForeColor = [System.Drawing.Color]::Red
    }
})

# Execute Query
$btnExecute.Add_Click({
    try {
        $lblStatus.Text = "Executing query..."
        $lblStatus.ForeColor = [System.Drawing.Color]::Blue
        $form.Refresh()

        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        $connString = Get-ConnectionString
        $conn = New-Object System.Data.SqlClient.SqlConnection($connString)
        $conn.Open()

        $cmd = New-Object System.Data.SqlClient.SqlCommand($txtQuery.Text, $conn)
        $cmd.CommandTimeout = 300

        $adapter = New-Object System.Data.SqlClient.SqlDataAdapter($cmd)
        $dataTable = New-Object System.Data.DataTable
        $rowCount = $adapter.Fill($dataTable)

        $conn.Close()
        $stopwatch.Stop()

        $dataGrid.DataSource = $dataTable
        $script:lastResults = $dataTable

        $elapsed = [math]::Round($stopwatch.Elapsed.TotalSeconds, 2)
        $lblStatus.Text = "Query completed: $rowCount rows returned in $elapsed seconds"
        $lblStatus.ForeColor = [System.Drawing.Color]::Green
    }
    catch {
        $lblStatus.Text = "Error: $($_.Exception.Message)"
        $lblStatus.ForeColor = [System.Drawing.Color]::Red
    }
})

# Clear Results
$btnClear.Add_Click({
    $dataGrid.DataSource = $null
    $script:lastResults = $null
    $lblStatus.Text = "Ready"
    $lblStatus.ForeColor = [System.Drawing.Color]::Black
})

# Export to CSV
$btnExport.Add_Click({
    if ($null -eq $script:lastResults -or $script:lastResults.Rows.Count -eq 0) {
        $lblStatus.Text = "No results to export"
        $lblStatus.ForeColor = [System.Drawing.Color]::Orange
        return
    }

    $saveDialog = New-Object System.Windows.Forms.SaveFileDialog
    $saveDialog.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
    $saveDialog.DefaultExt = "csv"
    $saveDialog.FileName = "query_results_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    $saveDialog.InitialDirectory = [Environment]::GetFolderPath("Desktop")

    if ($saveDialog.ShowDialog() -eq "OK") {
        try {
            $script:lastResults | Export-Csv -Path $saveDialog.FileName -NoTypeInformation
            $lblStatus.Text = "Exported to: $($saveDialog.FileName)"
            $lblStatus.ForeColor = [System.Drawing.Color]::Green
        }
        catch {
            $lblStatus.Text = "Export failed: $($_.Exception.Message)"
            $lblStatus.ForeColor = [System.Drawing.Color]::Red
        }
    }
})

# Handle form resize
$form.Add_Resize({
    $width = $form.ClientSize.Width - 20
    $connPanel.Width = $width
    $queryPanel.Width = $width
    $txtQuery.Width = $width - 20
    $lblStatus.Width = $width
    $dataGrid.Width = $width
    $dataGrid.Height = $form.ClientSize.Height - 320
})

# Show the form
[void]$form.ShowDialog()
