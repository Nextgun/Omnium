using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Omnium.UI.Services;

namespace Omnium.UI;

public partial class MainWindow : Window
{
    private readonly ApiClient _api = new();
    private int _selectedAssetId;
    private string _selectedSymbol = "";
    private const int DefaultAccountId = 1;
    private System.Windows.Threading.DispatcherTimer? _refreshTimer;

    public string LoggedInUser { get; set; } = "";

    public MainWindow()
    {
        InitializeComponent();
        Loaded += async (_, _) => await InitializeAsync();
    }

    private async Task InitializeAsync()
    {
        // Check API connection
        var healthy = await _api.HealthCheckAsync();
        if (healthy)
        {
            StatusDot.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
            StatusText.Text = "Connected";
        }
        else
        {
            StatusDot.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));
            StatusText.Text = "[E-201] API Offline — start Flask server";
        }

        // Load account info
        await RefreshAccountInfoAsync();

        // Show logged-in user
        if (UserNameText != null && !string.IsNullOrEmpty(LoggedInUser))
            UserNameText.Text = LoggedInUser;

        // Start auto-refresh timer (10s)
        _refreshTimer = new System.Windows.Threading.DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(10)
        };
        _refreshTimer.Tick += async (_, _) => await AutoRefreshAsync();
        _refreshTimer.Start();
    }

    private async Task AutoRefreshAsync()
    {
        if (_selectedAssetId <= 0) return;

        try
        {
        var price = await _api.GetLatestPriceAsync(_selectedAssetId);
        if (price != null)
            AssetPriceText.Text = $"${price.Close:F2}";

        var status = await _api.GetTradingStatusAsync(DefaultAccountId, _selectedAssetId);
        if (status != null)
        {
            SignalText.Text = status.Signal;
            SignalText.Foreground = new SolidColorBrush(status.Signal switch
            {
                "BUY" => (Color)ColorConverter.ConvertFromString("#10B981"),
                "SELL" => (Color)ColorConverter.ConvertFromString("#EF4444"),
                _ => (Color)ColorConverter.ConvertFromString("#8FA1C7")
            });
            SharesHeldText.Text = status.Shares_Held.ToString();
        }

        await RefreshAccountInfoAsync();
        StatusBarText.Text = $"Last refresh: {DateTime.Now:HH:mm:ss}";
        }
        catch
        {
            StatusBarText.Text = $"[E-201] Refresh failed at {DateTime.Now:HH:mm:ss} — API may be offline";
        }
    }

    // ── Navigation ──

    private void ShowPanel(string panel)
    {
        DashboardPanel.Visibility = panel == "dashboard" ? Visibility.Visible : Visibility.Collapsed;
        TradePanel.Visibility = panel == "trade" ? Visibility.Visible : Visibility.Collapsed;
        BacktestPanel.Visibility = panel == "backtest" ? Visibility.Visible : Visibility.Collapsed;
        EvaluatePanel.Visibility = panel == "evaluate" ? Visibility.Visible : Visibility.Collapsed;
        AccountPanel.Visibility = panel == "account" ? Visibility.Visible : Visibility.Collapsed;
        ConfigPanel.Visibility = panel == "config" ? Visibility.Visible : Visibility.Collapsed;
        PortfolioPanel.Visibility = panel == "portfolio" ? Visibility.Visible : Visibility.Collapsed;
        AboutPanel.Visibility = panel == "about" ? Visibility.Visible : Visibility.Collapsed;
    }

    private void NavDashboard_Click(object sender, RoutedEventArgs e) => ShowPanel("dashboard");

    private void NavTrade_Click(object sender, RoutedEventArgs e)
    {
        TradeAssetLabel.Text = _selectedAssetId > 0
            ? $"Asset: {_selectedSymbol} (ID: {_selectedAssetId})"
            : "No asset selected — search for one first";
        ShowPanel("trade");
    }

    private void NavBacktest_Click(object sender, RoutedEventArgs e)
    {
        BacktestAssetLabel.Text = _selectedAssetId > 0
            ? $"Asset: {_selectedSymbol} (ID: {_selectedAssetId})"
            : "No asset selected — search for one first";
        BacktestResultText.Text = "";
        ShowPanel("backtest");
    }

    private void NavEvaluate_Click(object sender, RoutedEventArgs e)
    {
        EvalAssetLabel.Text = _selectedAssetId > 0
            ? $"Asset: {_selectedSymbol} (ID: {_selectedAssetId})"
            : "No asset selected — search for one first";
        EvalSummaryText.Text = "";
        EvalResultGrid.Visibility = Visibility.Collapsed;
        ShowPanel("evaluate");
    }

    private async void NavAccount_Click(object sender, RoutedEventArgs e)
    {
        ShowPanel("account");
        AccountDetailText.Text = "Loading...";

        var account = await _api.GetAccountAsync(DefaultAccountId);
        if (account != null)
        {
            var trades = await _api.GetTradesAsync(DefaultAccountId);
            AccountDetailText.Text =
                $"Account ID: {account.Id}\n" +
                $"Type: {account.Type}\n" +
                $"Cash Balance: ${account.Cash_Balance:N2}\n" +
                $"Created: {account.Created_At}\n" +
                $"Total Trades: {trades.Count}";
        }
        else
        {
            AccountDetailText.Text = "[E-202] Could not load account. Is the API running?";
        }
    }

    private async void NavConfig_Click(object sender, RoutedEventArgs e)
    {
        ShowPanel("config");
        ConfigDetailText.Text = "Loading...";

        var config = await _api.GetTradingConfigAsync();
        if (config != null)
        {
            ConfigDetailText.Text =
                $"Active Algorithm: {config.Algorithm}\n" +
                $"Buy Threshold: {config.Buy_Threshold}%\n" +
                $"Sell Threshold: {config.Sell_Threshold}%\n" +
                $"Stop Loss: {config.Stop_Loss}%\n" +
                $"Max Position: {config.Max_Position} shares";
        }
        else
        {
            ConfigDetailText.Text = "[E-203] Could not load config. Is the API running?";
        }
    }

    private async void NavPortfolio_Click(object sender, RoutedEventArgs e)
    {
        ShowPanel("portfolio");
        PortfolioSummaryText.Text = "Loading positions...";

        var account = await _api.GetAccountAsync(DefaultAccountId);
        var trades = await _api.GetTradesAsync(DefaultAccountId);

        if (account == null)
        {
            PortfolioSummaryText.Text = "[E-204] Could not load account.";
            return;
        }

        // Calculate positions from trade history
        var positions = new Dictionary<int, (string Symbol, int Shares, decimal TotalCost)>();
        foreach (var t in trades)
        {
            if (!positions.ContainsKey(t.Asset_Id))
                positions[t.Asset_Id] = ("Asset " + t.Asset_Id, 0, 0m);

            var p = positions[t.Asset_Id];
            if (t.Side == "BUY")
                positions[t.Asset_Id] = (p.Symbol, p.Shares + t.Quantity, p.TotalCost + (decimal)(t.Price * t.Quantity));
            else
                positions[t.Asset_Id] = (p.Symbol, p.Shares - t.Quantity, p.TotalCost - (decimal)(t.Price * t.Quantity));
        }

        var items = new List<PortfolioItem>();
        foreach (var kvp in positions.Where(p => p.Value.Shares > 0))
        {
            var latest = await _api.GetLatestPriceAsync(kvp.Key);
            var currentValue = latest != null ? (decimal)latest.Close * kvp.Value.Shares : 0m;
            items.Add(new PortfolioItem
            {
                Symbol = kvp.Value.Symbol,
                Shares = $"{kvp.Value.Shares} shares",
                Value = $"${currentValue:N2}",
                PnL = $"Cost: ${kvp.Value.TotalCost:N2}"
            });
        }

        PortfolioList.ItemsSource = items;
        PortfolioSummaryText.Text = $"Cash: ${account.Cash_Balance:N2} | {items.Count} position(s)";
    }

    private void NavAbout_Click(object sender, RoutedEventArgs e) => ShowPanel("about");

    // ── Search ──

    private async void SearchButton_Click(object sender, RoutedEventArgs e) => await DoSearchAsync();

    private async void SearchBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) await DoSearchAsync();
    }

    private async Task DoSearchAsync()
    {
        var query = SearchBox.Text.Trim();
        if (string.IsNullOrEmpty(query)) return;

        SidebarStatus.Text = $"Searching '{query}'...";
        var results = await _api.SearchAssetsAsync(query);
        SearchResultsList.ItemsSource = results;
        SidebarStatus.Text = $"Found {results.Count} result(s)";
    }

    private async void SearchResultsList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (SearchResultsList.SelectedItem is not AssetDto asset) return;

        _selectedAssetId = asset.Id;
        _selectedSymbol = asset.Symbol;

        // Update dashboard
        AssetSymbolText.Text = asset.Symbol;
        AssetNameText.Text = asset.Name;
        SidebarStatus.Text = $"Selected: {asset.Symbol}";

        // Load price
        var price = await _api.GetLatestPriceAsync(asset.Id);
        AssetPriceText.Text = price != null ? $"${price.Close:F2}" : "--";

        // Load trading signal
        var status = await _api.GetTradingStatusAsync(DefaultAccountId, asset.Id);
        if (status != null)
        {
            SignalText.Text = status.Signal;
            SignalText.Foreground = new SolidColorBrush(status.Signal switch
            {
                "BUY" => (Color)ColorConverter.ConvertFromString("#10B981"),
                "SELL" => (Color)ColorConverter.ConvertFromString("#EF4444"),
                _ => (Color)ColorConverter.ConvertFromString("#8FA1C7")
            });
            SignalAlgoText.Text = $"Algorithm: {status.Algorithm}";
            SharesHeldText.Text = status.Shares_Held.ToString();
        }

        // Load price history
        var history = await _api.GetPriceHistoryAsync(asset.Id, 15);
        PriceHistoryList.ItemsSource = history;

        // Load trades for this asset
        var trades = await _api.GetTradesAsync(DefaultAccountId);
        TradeHistoryList.ItemsSource = trades.Where(t => t.Asset_Id == asset.Id).Take(20).ToList();

        ShowPanel("dashboard");
    }

    // ── Trading ──

    private async void RunTick_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            TradeResultText.Text = "[E-300] Select an asset first.";
            return;
        }

        var confirm = MessageBox.Show(
            $"Run trading algorithm on {_selectedSymbol}?\nThis may execute a buy or sell order.",
            "Confirm Trade", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (confirm != MessageBoxResult.Yes) return;

        TradeResultText.Text = "Running algorithm...";
        var result = await _api.TradingTickAsync(DefaultAccountId, _selectedAssetId);
        if (result != null)
        {
            TradeResultText.Text = result.Message;
            TradeResultText.Foreground = new SolidColorBrush(result.Action switch
            {
                "BUY" => (Color)ColorConverter.ConvertFromString("#10B981"),
                "SELL" => (Color)ColorConverter.ConvertFromString("#EF4444"),
                _ => (Color)ColorConverter.ConvertFromString("#8FA1C7")
            });
            await RefreshAccountInfoAsync();
        }
        else
        {
            TradeResultText.Text = "[E-301] Trade failed — is the API running?";
        }
    }

    // ── Backtest ──

    private async void RunBacktest_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            BacktestResultText.Text = "[E-300] Select an asset first.";
            return;
        }

        BacktestResultText.Text = "Running backtest...";
        var result = await _api.RunBacktestAsync(_selectedAssetId);
        if (result != null)
        {
            BacktestResultText.Text =
                $"Symbol: {result.Symbol}\n" +
                $"Algorithm: {result.Algorithm}\n" +
                $"Starting Cash: ${result.Starting_Cash:N2}\n" +
                $"Ending Cash: ${result.Ending_Cash:N2}\n" +
                $"Total Value: ${result.Total_Value:N2}\n" +
                $"Return: {result.Return_Pct}%\n" +
                $"Trades: {result.Total_Trades} ({result.Buys} buys, {result.Sells} sells)\n" +
                $"Shares Held: {result.Shares_Held}";
        }
        else
        {
            BacktestResultText.Text = "[E-302] Backtest failed — is the API running?";
        }
    }

    // ── Evaluate ──

    private async void RunEvaluate_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            EvalSummaryText.Text = "[E-300] Select an asset first.";
            return;
        }

        EvalSummaryText.Text = "Comparing strategies...";
        EvalResultGrid.Visibility = Visibility.Collapsed;
        var result = await _api.CompareAlgorithmsAsync(_selectedAssetId);
        if (result.HasValue)
        {
            var json = result.Value;
            EvalSummaryText.Text = $"Best: {json.GetProperty("best_strategy")} ({json.GetProperty("best_return_pct")}% return) | {json.GetProperty("bars_tested")} bars";

            var items = new List<EvalRow>();
            if (json.TryGetProperty("results", out var results))
            {
                foreach (var prop in results.EnumerateObject())
                {
                    var r = prop.Value;
                    items.Add(new EvalRow
                    {
                        Strategy = prop.Name,
                        ReturnPct = r.GetProperty("return_pct").ToString() + "%",
                        TotalValue = "$" + r.GetProperty("total_value"),
                        Trades = r.GetProperty("total_trades").ToString(),
                        Buys = r.TryGetProperty("buys", out var b) ? b.ToString() : "--",
                        Sells = r.TryGetProperty("sells", out var s) ? s.ToString() : "--"
                    });
                }
            }
            EvalResultGrid.ItemsSource = items;
            EvalResultGrid.Visibility = Visibility.Visible;
        }
        else
        {
            EvalSummaryText.Text = "[E-303] Evaluation failed — is the API running?";
            EvalSummaryText.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));
        }
    }

    // ── Helpers ──

    private async Task RefreshAccountInfoAsync()
    {
        var account = await _api.GetAccountAsync(DefaultAccountId);
        AccountCashText.Text = account != null ? $"${account.Cash_Balance:N2}" : "--";
    }
}

public class PortfolioItem
{
    public string Symbol { get; set; } = "";
    public string Shares { get; set; } = "";
    public string Value { get; set; } = "";
    public string PnL { get; set; } = "";
}

public class EvalRow
{
    public string Strategy { get; set; } = "";
    public string ReturnPct { get; set; } = "";
    public string TotalValue { get; set; } = "";
    public string Trades { get; set; } = "";
    public string Buys { get; set; } = "";
    public string Sells { get; set; } = "";
}
