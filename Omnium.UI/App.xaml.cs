using System.Windows;

namespace Omnium.UI;

public partial class App : Application
{
    private void Application_Startup(object sender, StartupEventArgs e)
    {
        ShutdownMode = ShutdownMode.OnExplicitShutdown;

        var login = new LoginWindow();
        if (login.ShowDialog() == true)
        {
            ShutdownMode = ShutdownMode.OnMainWindowClose;
            var main = new MainWindow();
            main.LoggedInUser = login.LoggedInUser;
            MainWindow = main;
            main.Show();
        }
        else
        {
            Shutdown();
        }
    }
}
