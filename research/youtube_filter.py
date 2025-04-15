from research.filtered_videos_analysis import titles_analysis, thumbnails_analysis

def youtube_filter(aggregated_videos):    
    K = 7
    beta = 0.01

    for video in aggregated_videos:
        try:
            views = int(video.get("viewCount", "0"))
        except ValueError:
            views = 0
        try:
            likes = int(video.get("likeCount", "0")) if video.get("likeCount") is not None else 0
        except ValueError:
            likes = 0
        age = video.get("age", 0)
        
        score = views / (age + K) + beta * likes
        
        video["score"] = score

    sorted_videos = sorted(aggregated_videos, key=lambda x: x.get("score", 0), reverse=True)[:10]
    
    filtered_videos = [{"title": video["title"], "thumbnail": video["thumbnail"]} for video in sorted_videos]

    titles_analysis(filtered_videos)
    thumbnails_analysis(filtered_videos)
    
    return filtered_videos