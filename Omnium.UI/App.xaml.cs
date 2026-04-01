using System.Windows;

namespace Omnium.UI;

public partial class App : Application
{
    private void Application_Startup(object sender, StartupEventArgs e)
    {
        var login = new LoginWindow();
        if (login.ShowDialog() == true)
        {
            var main = new MainWindow();
            main.LoggedInUser = login.LoggedInUser;
            main.Show();
        }
        else
        {
            Shutdown();
        }
    }
}
