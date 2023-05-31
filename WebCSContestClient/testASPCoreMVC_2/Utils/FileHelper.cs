using System.IO;

namespace testASPCoreMVC_2.Utils
{
    public class FileHelper
    {
        public async Task<string> readCodeAsync(String filePath) 
        {
            String stringCode = "print(int(input()) + 1)";
            using (StreamReader reader = new StreamReader(filePath))
            {
                stringCode = await reader.ReadToEndAsync();
                Console.WriteLine(stringCode);
            }

            return stringCode.Replace("\r", "");
        }
    }
}
