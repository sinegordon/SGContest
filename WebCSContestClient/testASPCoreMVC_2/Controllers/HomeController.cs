using Microsoft.AspNetCore.Mvc;
using Microsoft.Build.Evaluation;
using Newtonsoft.Json;
using System.Diagnostics;
using testASPCoreMVC_2.Areas.Admin.Models;
using testASPCoreMVC_2.Enums;
using testASPCoreMVC_2.Models;
using testASPCoreMVC_2.Utils;

namespace testASPCoreMVC_2.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        HomeIndexModel indexModel = new HomeIndexModel();
        APIHelper apiHelper = new APIHelper();
        FileHelper fileHelper = new FileHelper();

        private Microsoft.AspNetCore.Hosting.IHostingEnvironment Environment;

        public HomeController(ILogger<HomeController> logger)
        {
            _logger = logger;
        }

        [HttpGet]
        public IActionResult Index()
        {
            
            return View(indexModel);
        }

        [HttpGet]
        public IActionResult About()
        {
            return View();
        }

        [HttpGet]
        public IActionResult SignOut()
        {
            return Redirect("~/");
        }

        [HttpPost]
        public async Task<IActionResult> IndexAsync(string studentNameInput)
        {            
            var resp = await apiHelper.getOneUserAsync(studentNameInput);
            var userJson = System.Text.Json.JsonSerializer.Deserialize<UserJson>(resp);
            var user = userJson.getUser();
            indexModel.User = user.UserName;
            indexModel.tests = user.Data.Tests.ToList();
            indexModel.currentProblem = Int32.Parse(indexModel.tests[0].Variants.ElementAt(0).Key);
            indexModel.filePath = "F:\\SGContest-master\\PythonContestClient\\test.py";

            return View(indexModel);
        }

        [HttpPost]
        public async Task<IActionResult> Test(int currentProblem, String code, String studentNameInput, Languages LanguagesDD)
        {
            ViewBag.Message = "";
            //IFormFileCollection files = this.Request.Form.Files;
            //var req = this.Request;
            String testId = Guid.NewGuid().ToString();
            //String ?code = await fileHelper.readCodeAsync(filePath);
            String lang = "";

            //string wwwPath = this.Environment.WebRootPath;
            // contentPath = this.Environment.ContentRootPath;

            //string path = Path.Combine("", "Uploads");
            //if (!Directory.Exists(path))
            //{
            //    Directory.CreateDirectory(path);
            //}

            List<string> uploadedFiles = new List<string>();
            //string fileName = Path.GetFileName(srcFile.FileName);
            //using (FileStream stream = new FileStream(Path.Combine(path, fileName), FileMode.Create))
            //{
            //    srcFile.CopyTo(stream);
            //    if (stream is not null)
            //    {
            //        StreamReader reader = new StreamReader(stream);
            //        code = reader.ReadToEnd();
            //    }
            //}
            switch (LanguagesDD)
            {
                case Languages.python:
                    {
                        lang = LanguagesDD.ToString();
                        break;
                    }
                case Languages.cs:
                    {
                        lang = "c#";
                        break;
                    }
                case Languages.c:
                    {
                        lang = LanguagesDD.ToString();
                        break;
                    }
                case Languages.cpp:
                    {
                        lang = "c++";
                        break;
                    }
                default: break;
            }
            var resp = await apiHelper.sendCodeToTestServerAsync(testId, studentNameInput, currentProblem, lang, "test", "1", code);
            Thread.Sleep(10000);

            String respResult = await apiHelper.getLastResultAsync(testId);
            //var json = System.Text.Json.JsonSerializer.Deserialize<ProblemsModel>(resp);
            var p1 = respResult.IndexOf("success_count");
            var p2 = respResult.LastIndexOf("timestamp");
            string part = respResult.Substring(p1, p2 - p1 - 1);
            //var userJson = System.Text.Json.JsonSerializer.Deserialize<UserJson>(resp);
            //var user = userJson.getUser();
            //indexModel.User = studentNameInput;
            //indexModel.tests = user.Data.Tests.ToList();
            //ViewBag.Message = part;
            var resp2 = await apiHelper.getOneUserAsync(studentNameInput);
            var userJson = System.Text.Json.JsonSerializer.Deserialize<UserJson>(resp2);
            var user = userJson.getUser();
            indexModel.User = user.UserName;
            indexModel.tests = user.Data.Tests.ToList();
            indexModel.currentProblem = currentProblem;
            //indexModel.SrcFile = srcFile;
            //indexModel.filePath = filePath;
            indexModel.result = part;
            return View("Index", indexModel);
        }

        protected IActionResult ProblemChanged(object sender) { ViewBag.Message = "123123"; return View(); }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new testASPCoreMVC_2.Models.ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}