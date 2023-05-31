using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using testASPCoreMVC_2.Areas.Admin.Models;
using ErrorViewModel = testASPCoreMVC_2.Areas.Admin.Models.ErrorViewModel;
using testASPCoreMVC_2.Utils;

namespace testASPCoreMVC_2.Areas.Admin.Controllers
{
    [Area("Admin")]
    public class AdminController : Controller
    {
        private readonly ILogger<AdminController> _logger;
        APIHelper apiHelper = new APIHelper();

        public AdminController(ILogger<AdminController> logger)
        {
            _logger = logger;
        }

        [HttpGet]
        public IActionResult Index()
        {
            return View();
        }

        [HttpGet]
        public IActionResult About()
        {
            return View("Index");
        }

        [HttpGet]
        public IActionResult SignOut()
        {
            return Redirect("~/");
        }

        [HttpGet]
        [Route("Admin/Problems")]
        public async Task<IActionResult> Problems()
        {
            var resp = await apiHelper.getProblemsAsync();
            var result = System.Text.Json.JsonSerializer.Deserialize<ProblemsModel>(resp);
            
            return View(result);
        }
        [HttpGet]
        [Route("Admin/Users")]
        public async Task<IActionResult> Users()
        {
            var resp = await apiHelper.getUsersAsync();
            var users = System.Text.Json.JsonSerializer.Deserialize<UsersModel>(resp);

            return View(users.getUserNames());
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}