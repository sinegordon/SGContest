using testASPCoreMVC_2.Areas.Admin.Models;
using testASPCoreMVC_2.Enums;

namespace testASPCoreMVC_2.Models
{
    public class HomeIndexModel
    {
        public string User { get; set; }
        public string filePath { get; set; }
        public Languages languages;
        public Courses courses;
        public int currentProblem;

        public List<Test> tests;
        public String result = "";
        public IFormFile SrcFile;
        //public List<int> problems = new List<int>{1,2,3,4,5,6,7,8,9,10};
        //public List<int> variants = new List<int> { 1};
    }
}
