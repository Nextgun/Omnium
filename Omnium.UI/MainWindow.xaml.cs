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
            StatusText.Text = "API Offline — start Flask server";
        }

        // Load account info
        await RefreshAccountInfoAsync();
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
    }

    private void NavDashboard_Click(object sender, RoutedEventArgs e) => ShowPanel("dashboard");

    private void NavTrade_Click(object sender, RoutedEventArgs e)
    {
        TradeAssetLabel.Text = _selectedAssetId > 0
            ? $"Asset: {_selectedSymbol} (ID: {_selectedAssetId})"
            : "No asset selected — search for one first";
        ShowPanel("trade");
    }

    private async void NavBacktest_Click(object sender, RoutedEventArgs e)
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
        EvalResultText.Text = "";
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
            AccountDetailText.Text = "Could not load account. Is the API running?";
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
            ConfigDetailText.Text = "Could not load config. Is the API running?";
        }
    }

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
            TradeResultText.Text = "Select an asset first.";
            return;
        }

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
            TradeResultText.Text = "API error — is the server running?";
        }
    }

    // ── Backtest ──

    private async void RunBacktest_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            BacktestResultText.Text = "Select an asset first.";
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
            BacktestResultText.Text = "Backtest failed — is the API running?";
        }
    }

    // ── Evaluate ──

    private async void RunEvaluate_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            EvalResultText.Text = "Select an asset first.";
            return;
        }

        EvalResultText.Text = "Comparing strategies...";
        var result = await _api.CompareAlgorithmsAsync(_selectedAssetId);
        if (result.HasValue)
        {
            var json = result.Value;
            var lines = new System.Text.StringBuilder();
            lines.AppendLine($"Bars tested: {json.GetProperty("bars_tested")}");
            lines.AppendLine($"Best strategy: {json.GetProperty("best_strategy")}");
            lines.AppendLine($"Best return: {json.GetProperty("best_return_pct")}%");
            lines.AppendLine();

            if (json.TryGetProperty("results", out var results))
            {
                foreach (var prop in results.EnumerateObject())
                {
                    var r = prop.Value;
                    lines.AppendLine($"── {prop.Name} ──");
                    lines.AppendLine($"  Return: {r.GetProperty("return_pct")}%");
                    lines.AppendLine($"  Total Value: ${r.GetProperty("total_value")}");
                    lines.AppendLine($"  Trades: {r.GetProperty("total_trades")}");
                }
            }

            EvalResultText.Text = lines.ToString();
        }
        else
        {
            EvalResultText.Text = "Evaluation failed — is the API running?";
        }
    }

    // ── Helpers ──

    private async Task RefreshAccountInfoAsync()
    {
        var account = await _api.GetAccountAsync(DefaultAccountId);
        AccountCashText.Text = account != null ? $"${account.Cash_Balance:N2}" : "--";
    }
}
