using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using Omnium.UI.Services;

namespace Omnium.UI;

public partial class LoginWindow : Window
{
    private readonly ApiClient _api = new();
    private string _pendingUsername = "";

    public string LoggedInUser { get; private set; } = "";

    public LoginWindow()
    {
        InitializeComponent();
        UsernameBox.Focus();
    }

    private void Tab_Changed(object sender, RoutedEventArgs e)
    {
        if (LoginTab == null || SubmitButton == null) return;

        bool isLogin = LoginTab.IsChecked == true;
        SubmitButton.Content = isLogin ? "Login" : "Register";
        PasswordHint.Visibility = isLogin ? Visibility.Collapsed : Visibility.Visible;
        EmailPanel.Visibility = isLogin ? Visibility.Collapsed : Visibility.Visible;
        VerifyPanel.Visibility = Visibility.Collapsed;
        StatusMessage.Text = "";
    }

    private async void Submit_Click(object sender, RoutedEventArgs e) => await DoSubmitAsync();

    private async void PasswordBox_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter) await DoSubmitAsync();
    }

    private async Task DoSubmitAsync()
    {
        var username = UsernameBox.Text.Trim();
        var password = PasswordBox.Password;

        if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
        {
            StatusMessage.Text = "Please enter username and password.";
            return;
        }

        SubmitButton.IsEnabled = false;
        StatusMessage.Foreground = (SolidColorBrush)FindResource("TextMuted");
        StatusMessage.Text = "Connecting...";

        bool isLogin = LoginTab.IsChecked == true;
        var result = isLogin
            ? await _api.LoginAsync(username, password)
            : await _api.RegisterAsync(username, password);

        SubmitButton.IsEnabled = true;

        if (result == null)
        {
            StatusMessage.Foreground = (SolidColorBrush)FindResource("AccentRed");
            StatusMessage.Text = "Could not connect to API. Is the Flask server running?";
            return;
        }

        if (result.Success)
        {
            if (!isLogin && !string.IsNullOrWhiteSpace(EmailBox.Text))
            {
                // Registration succeeded — send verification email
                _pendingUsername = username;
                StatusMessage.Foreground = (SolidColorBrush)FindResource("AccentGreen");
                StatusMessage.Text = "Registered! Sending verification email...";

                var emailResult = await _api.SendVerificationAsync(username, EmailBox.Text.Trim());
                if (emailResult?.Success == true)
                {
                    VerifyPanel.Visibility = Visibility.Visible;
                    StatusMessage.Text = "Verification code sent. Enter it below, or skip to continue.";
                    SubmitButton.Content = "Skip Verification";
                    return;
                }
                else
                {
                    StatusMessage.Text = "Registered! (Verification email failed — continuing without it)";
                }
            }

            LoggedInUser = username;
            DialogResult = true;
            Close();
        }
        else
        {
            StatusMessage.Foreground = (SolidColorBrush)FindResource("AccentRed");
            StatusMessage.Text = result.Message;
        }
    }

    private async void Verify_Click(object sender, RoutedEventArgs e)
    {
        var code = VerifyCodeBox.Text.Trim();
        if (string.IsNullOrEmpty(code)) return;

        VerifyBtn.IsEnabled = false;
        var result = await _api.VerifyEmailAsync(_pendingUsername, code);
        VerifyBtn.IsEnabled = true;

        if (result?.Success == true)
        {
            LoggedInUser = _pendingUsername;
            DialogResult = true;
            Close();
        }
        else
        {
            StatusMessage.Foreground = (SolidColorBrush)FindResource("AccentRed");
            StatusMessage.Text = result?.Message ?? "Verification failed.";
        }
    }
}
