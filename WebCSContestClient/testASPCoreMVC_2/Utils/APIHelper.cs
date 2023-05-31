using Newtonsoft.Json;
using System.Net;
using System.Text;
using testASPCoreMVC_2.Areas.Admin.Models;
using testASPCoreMVC_2.Enums;

namespace testASPCoreMVC_2.Utils
{
    public class APIHelper
    {
        //static HttpClient httpClient = new HttpClient();
        //public string _getUserInfoEndpoint = "http://localhost:57888/api/get_user_info";
        //public string _getCoursesDataEndpoint = "http://localhost:57888/api/get_courses_data";
        //public string _getLastResultEndpoint = "http://localhost:57888/api/get_message_result";
        //public string _testEndpoint = "http://localhost:57888/api/add_message";
        public string _getUserInfoEndpoint = "http://cluster.vstu.ru:57888/api/get_user_info";
        public string _getCoursesDataEndpoint = "http://cluster.vstu.ru:57888/api/get_courses_data";
        public string _getLastResultEndpoint = "http://cluster.vstu.ru:57888/api/get_message_result";
        public string _testEndpoint = "http://cluster.vstu.ru:57888/api/add_message";

        public async Task<String> getUsersAsync() {
            string json = JsonConvert.SerializeObject(new { user_name = "*" });
            return sendPost(_getUserInfoEndpoint, json);
        }

        public async Task<String> getOneUserAsync(string userName){
            string json = JsonConvert.SerializeObject(new { user_name = userName });
            return sendPost(_getUserInfoEndpoint, json);
        }

        public async Task<String> getProblemsAsync(){            
            string json = JsonConvert.SerializeObject(new { id = 1, mqtt_key = "234", user = "2321", type = "problems", data_key = "test", action = "get_data" });
            return sendPost(_getCoursesDataEndpoint, json);
        }

        public async Task<String> sendCodeToTestServerAsync(String testId, String username, int problemNumber, String languageString, String courseNumber, String variantNumber, String codeString)
        {
            
            string json = JsonConvert.SerializeObject(new 
            { 
                id = testId, mqtt_key = "234", user = username, 
                language = languageString, course = courseNumber, action = "test_problem", 
                problem = problemNumber, variant = variantNumber, code = codeString
            });
            /*{
                'id': id, 'mqtt_key': mqtt_key, 'user': self.user,
                    'language': language, 'course': course, 'action': 'test_problem',
                    'problem': self.get_problem_number(self.user_data["test"][problem - 1]), 'variant': variant, 'code': code}*/
            return sendPost(_testEndpoint, json);
        }

        public async Task<String> getLastResultAsync(String testId)
        {
            string json = JsonConvert.SerializeObject(new { id = testId });
            return sendPost(_getLastResultEndpoint, json);
        }

        /*public static async Task<HttpResponseMessage> getProblemsAsync()
        {
            // создаем JsonContent
            JsonContent content = JsonContent.Create(new UserModel { user_name = "*" });
            // отправляем запрос
            using var response = await httpClient.PostAsync("http://localhost:57888/api/get_user_info", content);
            Console.WriteLine(response);
            return response;
        }*/

        public string? sendPost(string endpoint, string json) {
            byte[] body = Encoding.UTF8.GetBytes(json);
            Console.WriteLine("post: " + json);

            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(endpoint);
            request.Method = "POST";
            request.ContentType = "application/json; charset=utf-8";
            request.ContentLength = body.Length;

            using (Stream stream = request.GetRequestStream())
            {
                stream.Write(body, 0, body.Length);
                stream.Close();
            }

            HttpWebResponse response = (HttpWebResponse)request.GetResponse();
            using var reader = new StreamReader(response.GetResponseStream());
            string content = reader.ReadToEnd();

            Console.WriteLine("ответ: " + content);
            return content;
        }
    }
}
