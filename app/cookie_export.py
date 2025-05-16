import os
import browser_cookie3
import http.cookiejar

def export_cookies():
    """
    Export cookies from Chrome/Chromium browser to a file that yt-dlp can use.
    """
    try:
        # Try to get cookies from Chrome/Chromium
        cookies = browser_cookie3.chrome(domain_name='.youtube.com')
        
        # Create a MozillaCookieJar object
        cookie_jar = http.cookiejar.MozillaCookieJar('youtube_cookies.txt')
        
        # Add cookies to the jar
        for cookie in cookies:
            cookie_jar.set_cookie(cookie)
        
        # Save cookies to file
        cookie_jar.save(ignore_discard=True, ignore_expires=True)
        print("Cookies exported successfully to youtube_cookies.txt")
        
    except Exception as e:
        print(f"Error exporting cookies: {str(e)}")
        print("\nAlternative method:")
        print("1. Install the 'Get cookies.txt' extension in Chrome")
        print("2. Go to youtube.com")
        print("3. Click the extension and save the cookies")
        print("4. Rename the file to 'youtube_cookies.txt'")

if __name__ == "__main__":
    export_cookies() 