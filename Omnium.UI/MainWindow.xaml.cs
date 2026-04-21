using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Microsoft.Win32;
using OxyPlot;
using OxyPlot.Axes;
using OxyPlot.Series;
using Omnium.UI.Services;

namespace Omnium.UI;

public partial class MainWindow : Window
{
    private readonly ApiClient _api = new();
    private int _selectedAssetId;
    private string _selectedSymbol = "";
    private int _accountId = 1;
    private System.Windows.Threading.DispatcherTimer? _refreshTimer;
    private int _browsePage = 1;
    private int _browseTotalPages = 1;
    private bool _isDarkTheme = true;
    private string _browseFilter = "";
    private BacktestResultDto? _lastBacktest;

    public string LoggedInUser { get; set; } = "";

    public MainWindow()
    {
        InitializeComponent();
        Loaded += async (_, _) => await InitializeAsync();
    }

    private async Task InitializeAsync()
    {
        var healthy = await _api.HealthCheckAsync();
        if (healthy)
        {
            StatusDot.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
            StatusText.Text = "Connected";
        }
        else
        {
            StatusDot.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));
            StatusText.Text = "API Offline";
        }

        await RefreshAccountInfoAsync();

        if (UserNameText != null && !string.IsNullOrEmpty(LoggedInUser))
            UserNameText.Text = LoggedInUser;

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

            var status = await _api.GetTradingStatusAsync(_accountId, _selectedAssetId);
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
            StatusBarText.Text = $"Refresh failed at {DateTime.Now:HH:mm:ss} — API may be offline";
        }
    }

    // ── Navigation ──

    private void ShowPanel(string panel)
    {
        DashboardPanel.Visibility = panel == "dashboard" ? Visibility.Visible : Visibility.Collapsed;
        BacktestPanel.Visibility = panel == "backtest" ? Visibility.Visible : Visibility.Collapsed;
        EvaluatePanel.Visibility = panel == "evaluate" ? Visibility.Visible : Visibility.Collapsed;
        PortfolioPanel.Visibility = panel == "portfolio" ? Visibility.Visible : Visibility.Collapsed;
        ChartPanel.Visibility = panel == "chart" ? Visibility.Visible : Visibility.Collapsed;
        BrowsePanel.Visibility = panel == "browse" ? Visibility.Visible : Visibility.Collapsed;
        SettingsPanel.Visibility = panel == "settings" ? Visibility.Visible : Visibility.Collapsed;
        AboutPanel.Visibility = panel == "about" ? Visibility.Visible : Visibility.Collapsed;
    }

    private void NavDashboard_Click(object sender, RoutedEventArgs e) => ShowPanel("dashboard");

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

    private async void NavSettings_Click(object sender, RoutedEventArgs e)
    {
        ShowPanel("settings");
        await LoadSettingsAsync();
    }

    private async void NavPortfolio_Click(object sender, RoutedEventArgs e)
    {
        ShowPanel("portfolio");
        PortfolioSummaryText.Text = "Loading positions...";

        var account = await _api.GetAccountAsync(_accountId);
        var trades = await _api.GetTradesAsync(_accountId);

        if (account == null)
        {
            PortfolioSummaryText.Text = "Could not load account.";
            return;
        }

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

        AssetSymbolText.Text = asset.Symbol;
        AssetNameText.Text = asset.Name;
        SidebarStatus.Text = $"Selected: {asset.Symbol}";

        var price = await _api.GetLatestPriceAsync(asset.Id);
        AssetPriceText.Text = price != null ? $"${price.Close:F2}" : "--";

        var status = await _api.GetTradingStatusAsync(_accountId, asset.Id);
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

        var history = await _api.GetPriceHistoryAsync(asset.Id, 15);
        PriceHistoryList.ItemsSource = history;

        var trades = await _api.GetTradesAsync(_accountId);
        TradeHistoryList.ItemsSource = trades.Where(t => t.Asset_Id == asset.Id).Take(20).ToList();

        ShowPanel("dashboard");
    }

    // ── Trading (integrated into Dashboard) ──

    private async void RunTick_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            TradeResultText.Text = "Select an asset first.";
            return;
        }

        var confirm = MessageBox.Show(
            $"Run trading algorithm on {_selectedSymbol}?\nThis may execute a buy or sell order.",
            "Confirm Trade", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (confirm != MessageBoxResult.Yes) return;

        RunTickBtn.IsEnabled = false;
        TradeResultText.Text = "Running algorithm...";
        var result = await _api.TradingTickAsync(_accountId, _selectedAssetId);
        RunTickBtn.IsEnabled = true;

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
            TradeResultText.Text = "Trade failed — is the API running?";
        }
    }

    // ── Backtest (with configurable days + export) ──

    private async void RunBacktest_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            BacktestResultText.Text = "Select an asset first.";
            return;
        }

        if (!int.TryParse(BacktestDaysBox.Text.Trim(), out int days) || days < 1)
        {
            BacktestResultText.Text = "Enter a valid number of days.";
            return;
        }

        RunBacktestBtn.IsEnabled = false;
        BacktestResultText.Text = "Running backtest...";
        var result = await _api.RunBacktestAsync(_selectedAssetId, days);
        RunBacktestBtn.IsEnabled = true;

        if (result != null)
        {
            _lastBacktest = result;
            BacktestResultText.Text =
                $"Symbol: {result.Symbol} | Algorithm: {result.Algorithm}\n" +
                $"Starting: ${result.Starting_Cash:N2} → Ending: ${result.Ending_Cash:N2}\n" +
                $"Total Value: ${result.Total_Value:N2} | Return: {result.Return_Pct}%\n" +
                $"Trades: {result.Total_Trades} ({result.Buys} buys, {result.Sells} sells) | Shares: {result.Shares_Held}";
            ExportBacktestBtn.Visibility = Visibility.Visible;
        }
        else
        {
            BacktestResultText.Text = "Backtest failed — is the API running?";
            ExportBacktestBtn.Visibility = Visibility.Collapsed;
        }
    }

    private void ExportBacktest_Click(object sender, RoutedEventArgs e)
    {
        if (_lastBacktest == null) return;

        var dialog = new SaveFileDialog
        {
            Filter = "CSV files (*.csv)|*.csv",
            FileName = $"backtest_{_lastBacktest.Symbol}_{DateTime.Now:yyyyMMdd}.csv"
        };

        if (dialog.ShowDialog() == true)
        {
            var r = _lastBacktest;
            var csv = "Field,Value\n" +
                      $"Symbol,{r.Symbol}\n" +
                      $"Algorithm,{r.Algorithm}\n" +
                      $"Starting Cash,{r.Starting_Cash:F2}\n" +
                      $"Ending Cash,{r.Ending_Cash:F2}\n" +
                      $"Total Value,{r.Total_Value:F2}\n" +
                      $"Return %,{r.Return_Pct}\n" +
                      $"Total Trades,{r.Total_Trades}\n" +
                      $"Buys,{r.Buys}\n" +
                      $"Sells,{r.Sells}\n" +
                      $"Shares Held,{r.Shares_Held}\n";
            File.WriteAllText(dialog.FileName, csv);
            StatusBarText.Text = $"Exported to {dialog.FileName}";
        }
    }

    // ── Evaluate ──

    private async void RunEvaluate_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedAssetId <= 0)
        {
            EvalSummaryText.Text = "Select an asset first.";
            return;
        }

        RunEvalBtn.IsEnabled = false;
        EvalSummaryText.Text = "Comparing strategies...";
        EvalResultGrid.Visibility = Visibility.Collapsed;
        var result = await _api.CompareAlgorithmsAsync(_selectedAssetId);
        RunEvalBtn.IsEnabled = true;

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
            EvalSummaryText.Text = "Evaluation failed — is the API running?";
            EvalSummaryText.Foreground = (SolidColorBrush)FindResource("AccentRed");
        }
    }

    // ── Chart ──

    private async void NavChart_Click(object sender, RoutedEventArgs e)
    {
        ShowPanel("chart");
        if (_selectedAssetId <= 0)
        {
            ChartAssetLabel.Text = "No asset selected — search for one first";
            return;
        }

        ChartAssetLabel.Text = $"Loading chart for {_selectedSymbol}...";
        var history = await _api.GetPriceHistoryAsync(_selectedAssetId, 90);
        if (history.Count == 0)
        {
            ChartAssetLabel.Text = "No price data available for chart.";
            return;
        }

        ChartAssetLabel.Text = $"{_selectedSymbol} — Close Price (last {history.Count} days)";
        history.Reverse();

        var cardBg = ((SolidColorBrush)FindResource("CardBg")).Color;
        var borderColor = ((SolidColorBrush)FindResource("CardBorder")).Color;
        var textColor = ((SolidColorBrush)FindResource("TextSecondary")).Color;
        var mutedColor = ((SolidColorBrush)FindResource("TextMuted")).Color;
        var accentColor = ((SolidColorBrush)FindResource("AccentBlue")).Color;
        var gridAlpha = _isDarkTheme ? (byte)40 : (byte)60;

        var model = new PlotModel
        {
            Background = OxyColor.FromRgb(cardBg.R, cardBg.G, cardBg.B),
            PlotAreaBorderColor = OxyColor.FromRgb(borderColor.R, borderColor.G, borderColor.B),
            TextColor = OxyColor.FromRgb(textColor.R, textColor.G, textColor.B),
        };

        var dateAxis = new DateTimeAxis
        {
            Position = AxisPosition.Bottom,
            StringFormat = "MM/dd",
            AxislineColor = OxyColor.FromRgb(borderColor.R, borderColor.G, borderColor.B),
            TicklineColor = OxyColor.FromRgb(borderColor.R, borderColor.G, borderColor.B),
            TextColor = OxyColor.FromRgb(mutedColor.R, mutedColor.G, mutedColor.B),
            MajorGridlineStyle = LineStyle.Dot,
            MajorGridlineColor = OxyColor.FromArgb(gridAlpha, borderColor.R, borderColor.G, borderColor.B),
        };
        model.Axes.Add(dateAxis);

        var valueAxis = new LinearAxis
        {
            Position = AxisPosition.Left,
            StringFormat = "$0.00",
            AxislineColor = OxyColor.FromRgb(borderColor.R, borderColor.G, borderColor.B),
            TicklineColor = OxyColor.FromRgb(borderColor.R, borderColor.G, borderColor.B),
            TextColor = OxyColor.FromRgb(mutedColor.R, mutedColor.G, mutedColor.B),
            MajorGridlineStyle = LineStyle.Dot,
            MajorGridlineColor = OxyColor.FromArgb(gridAlpha, borderColor.R, borderColor.G, borderColor.B),
        };
        model.Axes.Add(valueAxis);

        var series = new LineSeries
        {
            Color = OxyColor.FromRgb(accentColor.R, accentColor.G, accentColor.B),
            StrokeThickness = 2,
            MarkerType = MarkerType.Circle,
            MarkerSize = 3,
            MarkerFill = OxyColor.FromRgb(accentColor.R, accentColor.G, accentColor.B),
        };

        foreach (var p in history)
        {
            if (DateTime.TryParse(p.Timestamp, out var dt))
                series.Points.Add(new DataPoint(DateTimeAxis.ToDouble(dt), p.Close));
        }

        model.Series.Add(series);
        PriceChartView.Model = model;
    }

    // ── Browse (with filter) ──

    private async void NavBrowse_Click(object sender, RoutedEventArgs e)
    {
        ShowPanel("browse");
        await LoadBrowsePageAsync();
    }

    private async Task LoadBrowsePageAsync()
    {
        BrowsePageInfo.Text = "Loading...";

        if (!string.IsNullOrEmpty(_browseFilter))
        {
            var results = await _api.SearchAssetsAsync(_browseFilter);
            BrowseGrid.ItemsSource = results;
            BrowsePageInfo.Text = $"Filter: '{_browseFilter}' — {results.Count} result(s)";
            BrowsePageNum.Text = "Filtered";
            return;
        }

        var result = await _api.GetAssetsPaginatedAsync(_browsePage, 10);
        if (result == null)
        {
            BrowsePageInfo.Text = "Could not load stocks. Is the API running?";
            return;
        }

        _browseTotalPages = result.Total_Pages;
        BrowseGrid.ItemsSource = result.Assets;
        BrowsePageInfo.Text = $"Showing page {result.Page} of {result.Total_Pages} ({result.Total} stocks total)";
        BrowsePageNum.Text = $"Page {result.Page} / {result.Total_Pages}";
    }

    private async void BrowsePrev_Click(object sender, RoutedEventArgs e)
    {
        if (_browsePage > 1) { _browsePage--; await LoadBrowsePageAsync(); }
    }

    private async void BrowseNext_Click(object sender, RoutedEventArgs e)
    {
        if (_browsePage < _browseTotalPages) { _browsePage++; await LoadBrowsePageAsync(); }
    }

    private async void BrowseFilter_Click(object sender, RoutedEventArgs e)
    {
        _browseFilter = BrowseFilterBox.Text.Trim();
        _browsePage = 1;
        await LoadBrowsePageAsync();
    }

    private async void BrowseFilter_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) { _browseFilter = BrowseFilterBox.Text.Trim(); _browsePage = 1; await LoadBrowsePageAsync(); }
    }

    private async void BrowseClearFilter_Click(object sender, RoutedEventArgs e)
    {
        _browseFilter = "";
        BrowseFilterBox.Text = "";
        _browsePage = 1;
        await LoadBrowsePageAsync();
    }

    private async void BrowseGrid_DoubleClick(object sender, MouseButtonEventArgs e)
    {
        if (BrowseGrid.SelectedItem is AssetDto asset)
        {
            _selectedAssetId = asset.Id;
            _selectedSymbol = asset.Symbol;

            AssetSymbolText.Text = asset.Symbol;
            AssetNameText.Text = asset.Name;
            SidebarStatus.Text = $"Selected: {asset.Symbol}";

            var price = await _api.GetLatestPriceAsync(asset.Id);
            AssetPriceText.Text = price != null ? $"${price.Close:F2}" : "--";

            ShowPanel("dashboard");
        }
    }

    // ── Settings (merged Account + Config + Algorithm Switch) ──

    private async Task LoadSettingsAsync()
    {
        // Load account
        var account = await _api.GetAccountAsync(_accountId);
        if (account != null)
        {
            var trades = await _api.GetTradesAsync(_accountId);
            AccountDetailText.Text =
                $"Type: {account.Type} | Cash: ${account.Cash_Balance:N2} | Created: {account.Created_At} | Trades: {trades.Count}";
        }
        else
        {
            AccountDetailText.Text = "Could not load account.";
        }

        // Load config
        var config = await _api.GetTradingConfigAsync();
        if (config != null)
        {
            // Set combo to match active algorithm
            foreach (ComboBoxItem item in AlgorithmCombo.Items)
            {
                if (item.Content.ToString() == config.Algorithm)
                {
                    AlgorithmCombo.SelectedItem = item;
                    break;
                }
            }
            BuyThresholdBox.Text = config.Buy_Threshold.ToString();
            SellThresholdBox.Text = config.Sell_Threshold.ToString();
            StopLossBox.Text = config.Stop_Loss.ToString();
            MaxPositionBox.Text = config.Max_Position.ToString();
        }
    }

    private async void SwitchAlgorithm_Click(object sender, RoutedEventArgs e)
    {
        if (AlgorithmCombo.SelectedItem is not ComboBoxItem selected) return;
        var algo = selected.Content.ToString() ?? "cs";

        SwitchAlgoBtn.IsEnabled = false;
        var result = await _api.SwitchAlgorithmAsync(algo);
        SwitchAlgoBtn.IsEnabled = true;

        AlgoSwitchStatus.Text = result?.Active != null
            ? $"Switched to: {result.Active}"
            : result?.Error ?? "Switch failed";
    }

    private async void SaveConfig_Click(object sender, RoutedEventArgs e)
    {
        if (!double.TryParse(BuyThresholdBox.Text, out var buy) ||
            !double.TryParse(SellThresholdBox.Text, out var sell) ||
            !double.TryParse(StopLossBox.Text, out var stop) ||
            !int.TryParse(MaxPositionBox.Text, out var maxPos))
        {
            ConfigSaveStatus.Text = "Invalid values — enter numbers only.";
            return;
        }

        SaveConfigBtn.IsEnabled = false;
        var result = await _api.UpdateTradingConfigAsync(buy, sell, stop, maxPos);
        SaveConfigBtn.IsEnabled = true;

        ConfigSaveStatus.Text = result != null ? "Config saved." : "Save failed — is the API running?";
    }

    private async void AccountId_Changed(object sender, TextChangedEventArgs e)
    {
        if (int.TryParse(AccountIdBox.Text.Trim(), out int id) && id > 0)
        {
            _accountId = id;
            await RefreshAccountInfoAsync();
        }
    }

    // ── Theme Toggle ──

    private void ThemeToggle_Click(object sender, RoutedEventArgs e)
    {
        _isDarkTheme = !_isDarkTheme;
        var themePath = _isDarkTheme ? "Themes/DarkTheme.xaml" : "Themes/LightTheme.xaml";
        var newTheme = new ResourceDictionary { Source = new Uri(themePath, UriKind.Relative) };

        Application.Current.Resources.MergedDictionaries.Clear();
        Application.Current.Resources.MergedDictionaries.Add(newTheme);

        ThemeToggleBtn.Content = _isDarkTheme ? "\u2600" : "\u263D";

        var bg = new LinearGradientBrush
        {
            StartPoint = new Point(0.5, 0),
            EndPoint = new Point(0.5, 1)
        };
        bg.GradientStops.Add(new GradientStop((Color)FindResource("BgGradientTop"), 0));
        bg.GradientStops.Add(new GradientStop((Color)FindResource("BgGradientBottom"), 1));
        Background = bg;

        if (_selectedAssetId > 0 && ChartPanel.Visibility == Visibility.Visible)
            NavChart_Click(sender, e);
    }

    // ── Manual Refresh ──

    private async void ManualRefresh_Click(object sender, RoutedEventArgs e)
    {
        RefreshBtn.IsEnabled = false;
        await AutoRefreshAsync();
        RefreshBtn.IsEnabled = true;
    }

    // ── Helpers ──

    private async Task RefreshAccountInfoAsync()
    {
        var account = await _api.GetAccountAsync(_accountId);
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
