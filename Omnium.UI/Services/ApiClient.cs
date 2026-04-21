using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;

namespace Omnium.UI.Services;

/// <summary>
/// HTTP client for the Omnium Flask REST API (localhost:5000).
/// All methods return parsed JSON or null on failure.
/// </summary>
public class ApiClient
{
    private readonly HttpClient _http;
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public ApiClient(string baseUrl = "http://localhost:5000")
    {
        _http = new HttpClient { BaseAddress = new Uri(baseUrl) };
        _http.Timeout = TimeSpan.FromSeconds(10);
    }

    // ── Health ──

    public async Task<bool> HealthCheckAsync()
    {
        try
        {
            var resp = await _http.GetAsync("/health");
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    // ── Assets ──

    public async Task<List<AssetDto>> SearchAssetsAsync(string query)
    {
        try
        {
            var resp = await _http.GetAsync($"/assets/search?q={Uri.EscapeDataString(query)}");
            if (!resp.IsSuccessStatusCode) return new();
            return await resp.Content.ReadFromJsonAsync<List<AssetDto>>(JsonOpts) ?? new();
        }
        catch { return new(); }
    }

    public async Task<AssetDto?> GetAssetAsync(int assetId)
    {
        try
        {
            return await _http.GetFromJsonAsync<AssetDto>($"/assets/{assetId}", JsonOpts);
        }
        catch { return null; }
    }

    // ── Prices ──

    public async Task<PriceDto?> GetLatestPriceAsync(int assetId)
    {
        try
        {
            return await _http.GetFromJsonAsync<PriceDto>($"/prices/{assetId}/latest", JsonOpts);
        }
        catch { return null; }
    }

    public async Task<List<PriceDto>> GetPriceHistoryAsync(int assetId, int limit = 30)
    {
        try
        {
            return await _http.GetFromJsonAsync<List<PriceDto>>(
                $"/prices/{assetId}?limit={limit}", JsonOpts) ?? new();
        }
        catch { return new(); }
    }

    // ── Account ──

    public async Task<AccountDto?> GetAccountAsync(int accountId)
    {
        try
        {
            return await _http.GetFromJsonAsync<AccountDto>($"/account/{accountId}", JsonOpts);
        }
        catch { return null; }
    }

    public async Task<List<TradeDto>> GetTradesAsync(int accountId)
    {
        try
        {
            return await _http.GetFromJsonAsync<List<TradeDto>>(
                $"/account/{accountId}/trades", JsonOpts) ?? new();
        }
        catch { return new(); }
    }

    public async Task<PositionDto?> GetPositionAsync(int accountId, int assetId)
    {
        try
        {
            return await _http.GetFromJsonAsync<PositionDto>(
                $"/account/{accountId}/position/{assetId}", JsonOpts);
        }
        catch { return null; }
    }

    // ── Auth ──

    public async Task<AuthResultDto?> RegisterAsync(string username, string password)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/auth/register",
                new { username, password });
            return await resp.Content.ReadFromJsonAsync<AuthResultDto>(JsonOpts);
        }
        catch { return null; }
    }

    public async Task<AuthResultDto?> LoginAsync(string username, string password)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/auth/login",
                new { username, password });
            return await resp.Content.ReadFromJsonAsync<AuthResultDto>(JsonOpts);
        }
        catch { return null; }
    }

    // ── Trading ──

    public async Task<TickResultDto?> TradingTickAsync(int accountId, int assetId)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/trading/tick",
                new { account_id = accountId, asset_id = assetId });
            return await resp.Content.ReadFromJsonAsync<TickResultDto>(JsonOpts);
        }
        catch { return null; }
    }

    public async Task<TradingStatusDto?> GetTradingStatusAsync(int accountId, int assetId)
    {
        try
        {
            return await _http.GetFromJsonAsync<TradingStatusDto>(
                $"/trading/status/{accountId}/{assetId}", JsonOpts);
        }
        catch { return null; }
    }

    public async Task<TradingConfigDto?> GetTradingConfigAsync()
    {
        try
        {
            return await _http.GetFromJsonAsync<TradingConfigDto>("/trading/config", JsonOpts);
        }
        catch { return null; }
    }

    // ── Trading Config & Switch ──

    public async Task<TradingConfigDto?> UpdateTradingConfigAsync(double buyThreshold, double sellThreshold, double stopLoss, int maxPosition)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/trading/config",
                new { buy_threshold = buyThreshold, sell_threshold = sellThreshold, stop_loss = stopLoss, max_position = maxPosition });
            return await resp.Content.ReadFromJsonAsync<TradingConfigDto>(JsonOpts);
        }
        catch { return null; }
    }

    public async Task<SwitchResultDto?> SwitchAlgorithmAsync(string algorithm)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/trading/switch",
                new { algorithm });
            return await resp.Content.ReadFromJsonAsync<SwitchResultDto>(JsonOpts);
        }
        catch { return null; }
    }

    // ── Backtest ──

    public async Task<BacktestResultDto?> RunBacktestAsync(int assetId, int limit = 90)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/backtest/run",
                new { asset_id = assetId, limit });
            return await resp.Content.ReadFromJsonAsync<BacktestResultDto>(JsonOpts);
        }
        catch { return null; }
    }

    // ── Email Verification ──

    public async Task<AuthResultDto?> SendVerificationAsync(string username, string email)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/auth/send-verification",
                new { username, email });
            return await resp.Content.ReadFromJsonAsync<AuthResultDto>(JsonOpts);
        }
        catch { return null; }
    }

    public async Task<AuthResultDto?> VerifyEmailAsync(string username, string code)
    {
        try
        {
            var resp = await _http.PostAsJsonAsync("/auth/verify-email",
                new { username, code });
            return await resp.Content.ReadFromJsonAsync<AuthResultDto>(JsonOpts);
        }
        catch { return null; }
    }

    // ── Assets (paginated) ──

    public async Task<PaginatedAssetsDto?> GetAssetsPaginatedAsync(int page = 1, int perPage = 10)
    {
        try
        {
            return await _http.GetFromJsonAsync<PaginatedAssetsDto>(
                $"/assets?page={page}&per_page={perPage}", JsonOpts);
        }
        catch { return null; }
    }

    // ── Evaluation ──

    public async Task<JsonElement?> CompareAlgorithmsAsync(int assetId, int limit = 90)
    {
        try
        {
            return await _http.GetFromJsonAsync<JsonElement>(
                $"/evaluation/compare?asset_id={assetId}&limit={limit}", JsonOpts);
        }
        catch { return null; }
    }
}

// ── DTOs ──

public record AssetDto(int Id, string Symbol, string Name);
public record PriceDto(int Id, int Asset_Id, string? Timestamp, double Open, double High, double Low, double Close, long Volume);
public record AccountDto(int Id, string Type, double Cash_Balance, string? Created_At);
public record TradeDto(int Id, int Account_Id, int Asset_Id, string Side, int Quantity, double Price, string? Timestamp);
public record PositionDto(int Account_Id, int Asset_Id, int Shares);
public record AuthResultDto(bool Success, string Message);
public record TickResultDto(int Asset_Id, string Symbol, string Action, double Price, int Shares_Held, bool Trade_Executed, string Message);
public record TradingStatusDto(int Account_Id, int Asset_Id, string Symbol, double Current_Price, double Reference_Price, int Shares_Held, double? Avg_Buy_Price, string Signal, string Algorithm);
public record TradingConfigDto(string Algorithm, double Buy_Threshold, double Sell_Threshold, double Stop_Loss, int Max_Position);
public record BacktestResultDto(int Asset_Id, string Symbol, string Algorithm, double Starting_Cash, double Ending_Cash, int Shares_Held, double Total_Value, double Return_Pct, int Total_Trades, int Buys, int Sells);
public record PaginatedAssetsDto(List<AssetDto> Assets, int Page, int Per_Page, int Total, int Total_Pages);
public record SwitchResultDto(string? Active, string? Error);
