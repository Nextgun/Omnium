using System.Windows;
using System.Windows.Input;
using Omnium.UI.Services;

namespace Omnium.UI;

public partial class LoginWindow : Window
{
    private readonly ApiClient _api = new();

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
            StatusMessage.Text = "[E-101] Please enter username and password.";
            return;
        }

        SubmitButton.IsEnabled = false;
        StatusMessage.Foreground = System.Windows.Media.Brushes.Gray;
        StatusMessage.Text = "Connecting...";

        bool isLogin = LoginTab.IsChecked == true;
        var result = isLogin
            ? await _api.LoginAsync(username, password)
            : await _api.RegisterAsync(username, password);

        SubmitButton.IsEnabled = true;

        if (result == null)
        {
            StatusMessage.Foreground = System.Windows.Media.Brushes.OrangeRed;
            StatusMessage.Text = "[E-102] Could not connect to API. Is the Flask server running?";
            return;
        }

        if (result.Success)
        {
            LoggedInUser = username;
            DialogResult = true;
            Close();
        }
        else
        {
            StatusMessage.Foreground = System.Windows.Media.Brushes.OrangeRed;
            StatusMessage.Text = result.Message;
        }
    }
}
