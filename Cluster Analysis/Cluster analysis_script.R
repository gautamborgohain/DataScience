library(foreign)
library(lubridate)
library(data.table)
library(cluster)
library(reshape)
library(dummies)
library(fpc)
library(igraph)
library(psych)
library(ggplot2)
library(fpc)
library(gridExtra)
install.packages(c('data.table','cluster','reshape','dummies','fpc','igraph','psych','ggplot2','fpc','gridExtra'))
#read the spss file and extract the time
#   sample_release = read.spss(
#     '/Users/gautamborgohain/Google Drive/NTU/Social Media Analytics/sample 1 for release.sav', to.data.frame = T
#   )
sample_release = read.spss('/Users/gautamborgohain/Downloads/sample 2 for release.sav',to.data.frame = T)

sample_release = timeingdf
names(sample_release)[names(sample_release) == "Created.At"] = "datetime"
names(sample_release)[names(sample_release) == "ID"] = "user_id"

sample_releasedata = data.table(sample_release)
timedf = as.POSIXlt(sample_releasedata$datetime,origin = '1582-10-14',tz =
                      'GMT')


#Prepare the data table with the relevent time components
sample_releasedata$date = as.Date(timedf)
sample_releasedata$hour = timedf$hour
sample_releasedata$min = timedf$mi
sample_releasedata$sec = timedf$sec
sample_releasedata$mday = timedf$mday
sample_releasedata$year = timedf$year
sample_releasedata$wday = timedf$wday

#get data to represent user-wise values
r_agg_hr = cast(sample_releasedata[,(COUNT = .N),by = list(user_id,hour)], user_id ~ hour, mean, fill = 0)
r_agg_mi = cast(sample_releasedata[,(COUNT = .N),by = list(user_id,min)], user_id ~ min, mean, fill = 0)
r_agg_sec = cast(sample_releasedata[,(COUNT = .N),by = list(user_id,sec)], user_id ~ sec, mean, fill = 0)
r_agg_mday = cast(sample_releasedata[,(COUNT = .N),by = list(user_id,mday)], user_id ~ mday, mean, fill = 0)
r_agg_year = cast(sample_releasedata[,(COUNT = .N),by = list(user_id,year)], user_id ~ year, mean, fill = 0)
r_agg_wday = cast(sample_releasedata[,(COUNT = .N),by = list(user_id,wday)], user_id ~ wday, mean, fill = 0)




#This function prints the scree plot of the clusters and returns the value of the desirable cluster
wssplot = function(data, nc = 7, seed = 1234) {
  data = data[-1]#remove user id from cluster anlaysis
  wss = (nrow(data) - 1) * sum(apply(data,2,var))
  for (i in 2:nc) {
    set.seed(seed)
    wss[i] = sum(kmeans(data, centers = i)$withinss)
  }
  cluster = bestcluster(wss)
  print(cluster)
  print(dim_select(wss))#this is the one from the igraph implementation for M. Zhu, and A. Ghodsi (2006)
  #plot(1:nc, wss, type = "b", xlab = "Number of Clusters",ylab = "Within groups sum of squares")
  return (cluster)
}

#based on the withiness score provided by K means, this function return the the cluster where the "drop" of scores is less than 40%
bestcluster = function(scores) {
  for (i in 2:length(scores)) {
    difference = scores[i - 1] - scores[i]
    benchmark = scores[i - 1] * 0.35
    if (difference < benchmark) {
      return (i - 1)
    }
  }
}

#Replace outliers based on Mahalanobis distance - psych package
replaceOutliers <- function (df) {
  mydata = df[-1]
  outliers = outlier(mydata, plot = T)
  df.1 = data.table(df,outliers)
  #pairs.panels(df.1,bg=c("yellow","blue")[(outliers > 25)+1],pch=21)
  
  # Exclude the top 5 outliers
  temp = df.1[,.SD[order(-outliers)[6:nrow(df.1)]]]
  # remove the outlier column
  temp = temp[,outliers := NULL]
  return(data.frame(temp))
}

# 
# datalist = list(r_agg_hr,
#                 r_agg_mi,
#                 r_agg_sec,
#                 r_agg_mday,
#                 r_agg_year,
#                 r_agg_wday)


clusterAnalysis <- function (data,cluster,printanova) {
  #data = r_agg_hr
  wssplot(data,nc= 7)
  dfwithoutid = data[-1]#remove user id from cluster anlaysis
  fit = kmeans(dfwithoutid,cluster,nstart = 15)
  tempdata = data.frame(data)
  tempdata$cluster = fit$cluster
  tempdata$cluster = factor(tempdata$cluster)
  clustereddata = tempdata
  tempdata = tempdata[-1]#remove user id
  
  # Print out the anova and tukey stuff
  for(i in names(tempdata)){
    if(i == "cluster")
      break;
    anova = aov(as.formula(paste(i,"~cluster")), data = tempdata)
    if(printanova == T){
      print(paste("---------------Anova and Tukey HSD-------------",ifelse((ncol(tempdata)>10),"Hourly","Weekly")))
      print(i)
      print(summary(anova))
      print(TukeyHSD(anova))
    }
    
  }
  
  
#   #PCA plot comparrison
#   
#   clusplot(
#     data, fit$cluster, shade = T, lines = 0, color = T, lty = 4,main =
#       'Principal Components plot showing K-means clusters'
#   )
#   
#   #Centroid plot
#   plotcluster(data, fit$cluster, xlab = "Discriminant func 1", ylab = "Discriminant func 2")
#   
  return(clustereddata)
}


clusterAnlaysisOfWeekdays <- function (data, cluster, sample_releasedata, printanova = F) {
  
  cdf = clusterAnalysis(data,cluster,printanova)
  
  data = replaceOutliers(data)# removing top 5 outlier users
  cdf.1 = clusterAnalysis(data,cluster,printanova) #.1 variables are after removing outliers
  
  combineddf = merge(sample_releasedata,cdf, by = "user_id")
  combineddf.1 = merge(sample_releasedata,cdf.1, by = "user_id")
  
  combineddf$cluster = as.numeric(combineddf$cluster)
  combineddf.1$cluster = as.numeric(combineddf.1$cluster)
  
  
  cluster1 = combineddf[cluster == 1,(COUNT = .N), by= wday]
  cluster2 = combineddf[cluster == 2,(COUNT = .N), by= wday]
  cluster3 = combineddf[cluster == 3,(COUNT = .N), by= wday]
  
  
  #renaming the dfs
  names(cluster1)[names(cluster1)== "V1"]  = "Cluster 1"
  names(cluster2)[names(cluster2)== "V1"]  = "Cluster 2"
  names(cluster3)[names(cluster3)== "V1"]  = "Cluster 3"
  
  listdf = list(cluster1,cluster2,cluster3)
  
  
  #merge all into one final df for plotting
  finaldf = Reduce(function(...) merge(..., all=T,by = 'wday'), listdf)
  
  finalmelt = melt(finaldf,id = 'wday')
  names(finalmelt)[names(finalmelt)=="variable"] = "Clusters"
  plt1 = ggplot(data=finalmelt,
                aes(x=wday, y=value, colour=Clusters)) +
    geom_line(size=2)+
    theme_classic()+   theme(panel.background = element_rect(fill = "black"))+
    xlab("Days of a Week")+
    ylab("Frequency of tweets")+
    ggtitle("Difference in clusters' time for tweeting - Weekly")+
    scale_x_continuous(breaks = seq(0,6,1))
  
  #Taking the percentage data - orginal data
  finaldf[is.na(finaldf)] = 0
  finaldf$Cluster.1 = finaldf$`Cluster 1`/sum(finaldf$`Cluster 1`) *100
  finaldf$Cluster.2 = finaldf$`Cluster 2`/sum(finaldf$`Cluster 2`) *100
  finaldf$Cluster.3 = finaldf$`Cluster 3`/sum(finaldf$`Cluster 3`) *100
  
  
  names(finaldf)[names(finaldf)== "Cluster.1"]  = "All week user"
  names(finaldf)[names(finaldf)== "Cluster.2"]  = "Weekends user"
  names(finaldf)[names(finaldf)== "Cluster.3"]  = "Mid Week user"
  
  
  finaldf = data.frame(finaldf)
  finaldf = finaldf[-c(2:4)]
  finaldf = data.table(finaldf)
  
  
  finalmelt = melt(finaldf,id = 'wday')
  names(finalmelt)[names(finalmelt)=="variable"] = "Clusters"
  plt2 = ggplot(data=finalmelt,
                aes(x=wday, y=value, colour=Clusters)) +
    geom_line(size=2)+
    theme_classic()+   theme(panel.background = element_rect(fill = "black"))+
    xlab("Days of a Week")+
    ylab("Percentage of frequency of tweets %")+
    ggtitle("Difference in clusters' time for tweeting - Weekly - Percentage")+
    scale_x_continuous(breaks = seq(0,6,1))
  
  
  #After removing outliers:
  cluster1 = combineddf.1[cluster == 1,(COUNT = .N), by= wday]
  cluster2 = combineddf.1[cluster == 2,(COUNT = .N), by= wday]
  cluster3 = combineddf.1[cluster == 3,(COUNT = .N), by= wday]
  
  
  #renaming the dfs
  names(cluster1)[names(cluster1)== "V1"]  = "Cluster 1"
  names(cluster2)[names(cluster2)== "V1"]  = "Cluster 2"
  names(cluster3)[names(cluster3)== "V1"]  = "Cluster 3"
  
  if(cluster ==3){
    listdf = list(cluster1,cluster2,cluster3)
  }
  
  #merge all into one final df for plotting
  finaldf = Reduce(function(...) merge(..., all=T,by = 'wday'), listdf)
  
  finalmelt = melt(finaldf,id = 'wday')
  names(finalmelt)[names(finalmelt)=="variable"] = "Clusters"
  plt3 = ggplot(data=finalmelt,
                aes(x=wday, y=value, colour=Clusters)) +
    geom_line(size=2)+
    theme_classic()+   theme(panel.background = element_rect(fill = "black"))+
    xlab("Days of a Week")+
    ylab("Frequency of tweets")+
    ggtitle("Difference in clusters' time for tweeting - Weekly - Removed outliers")+
    scale_x_continuous(breaks = seq(0,6,1))
  
  
  grid.arrange(plt1,plt2,ncol=1, nrow = 2)
  print(plt1)
  print(plt2)
  weekdayclusters = combineddf
  return(list(weekdayclusters,cdf))
}



clusterAnlaysisOfHours <- function (data, cluster, sample_releasedata,printanova = F) {
  
  cdf = clusterAnalysis(data,cluster,printanova)
  print("After removing outliers")
  
  data = replaceOutliers(data)# removing top 5 outlier users
  
  cdf.1 = clusterAnalysis(data,cluster,printanova) #.1 variables are after removing outliers
  combineddf = merge(sample_releasedata,cdf, by = "user_id")
  combineddf.1 = merge(sample_releasedata,cdf.1, by = "user_id")
  
  combineddf$cluster = as.numeric(combineddf$cluster)
  combineddf.1$cluster = as.numeric(combineddf.1$cluster)
  
  #combineddf = hourclusters
  cluster1 = combineddf[cluster == 1,(COUNT = .N), by= hour]
  cluster2 = combineddf[cluster == 2,(COUNT = .N), by= hour]
  cluster3 = combineddf[cluster == 3,(COUNT = .N), by= hour]
  cluster4 = combineddf[cluster == 4,(COUNT = .N), by= hour]
  
  
  #renaming the dfs
  names(cluster1)[names(cluster1)== "V1"]  = "Cluster 1"
  names(cluster2)[names(cluster2)== "V1"]  = "Cluster 2"
  names(cluster3)[names(cluster3)== "V1"]  = "Cluster 3"
  names(cluster4)[names(cluster4)== "V1"]  = "Cluster 4"
  
  
  listdf = list(cluster1,cluster2,cluster3,cluster4)
  if(cluster ==3){
    listdf = list(cluster1,cluster2,cluster3)
  }
  
  #merge all into one final df for plotting
  finaldf = Reduce(function(...) merge(..., all=T,by = 'hour'), listdf)
  
  
  finalmelt = melt(finaldf,id = 'hour')
  names(finalmelt)[names(finalmelt)=="variable"] = "Clusters"
  plt1 = ggplot(data=finalmelt,
                aes(x=hour, y=value, colour=Clusters)) +
    geom_line(size=2)+
    theme_classic()+   theme(panel.background = element_rect(fill = "black"))+
    xlab("Hours of a day")+
    ylab("Frequency of tweets")+
    ggtitle("Difference in clusters' time for tweeting - Hourly")+
    scale_x_continuous(breaks = seq(0,24,1))
  #scale_y_continuous(breaks = seq(0,1500,25))
  
  #Taking the percentage data - orginal data
  
  #renaming the dfs
  
  listdf = list(cluster1,cluster2,cluster3,cluster4)
  finaldf = Reduce(function(...) merge(..., all=T,by = 'hour'), listdf)
  
  finaldf[is.na(finaldf)] = 0
  finaldf$Cluster.1 = finaldf$`Cluster 1`/sum(finaldf$`Cluster 1`) *100
  finaldf$Cluster.2 = finaldf$`Cluster 2`/sum(finaldf$`Cluster 2`) *100
  finaldf$Cluster.3 = finaldf$`Cluster 3`/sum(finaldf$`Cluster 3`) *100
  finaldf$Cluster.4 = finaldf$`Cluster 4`/sum(finaldf$`Cluster 4`) *100
  
  names(finaldf)[names(finaldf)== "Cluster.1"]  = "Early morning - All day - Late night"
  names(finaldf)[names(finaldf)== "Cluster.2"]  = "Afternoon - Late night"
  names(finaldf)[names(finaldf)== "Cluster.3"]  = "Lunch Break - After Work"
  names(finaldf)[names(finaldf)== "Cluster.4"]  = "Before Breakfast - After Dinner"
  
  finaldf = data.frame(finaldf)
  finaldf = finaldf[-c(2:5)]
  finaldf = data.table(finaldf)
  
  
  finalmelt = melt(finaldf,id = 'hour')
  names(finalmelt)[names(finalmelt)=="variable"] = "Clusters"
  plt2 = ggplot(data=finalmelt,
                aes(x=hour, y=value, colour=Clusters)) +
    geom_line(size=2)+
    theme_classic()+   theme(panel.background = element_rect(fill = "black"))+
    xlab("Hours of a day")+
    ylab("Percentage of frequency of tweets %")+
    ggtitle("Difference in clusters' time for tweeting - Hourly - Percentage")+
    scale_x_continuous(breaks = seq(0,24,1))
  
  
  #After removing outliers:
  cluster1 = combineddf.1[cluster == 1,(COUNT = .N), by= hour]
  cluster2 = combineddf.1[cluster == 2,(COUNT = .N), by= hour]
  cluster3 = combineddf.1[cluster == 3,(COUNT = .N), by= hour]
  cluster4 = combineddf.1[cluster == 4,(COUNT = .N), by= hour]
  
  #renaming the dfs
  names(cluster1)[names(cluster1)== "V1"]  = "Cluster 1"
  names(cluster2)[names(cluster2)== "V1"]  = "Cluster 2"
  names(cluster3)[names(cluster3)== "V1"]  = "Cluster 3"
  names(cluster4)[names(cluster4)== "V1"]  = "Cluster 4"
  
  listdf = list(cluster1,cluster2,cluster3,cluster4)
  if(cluster ==3){
    listdf = list(cluster1,cluster2,cluster3)
  }
  
  
  #merge all into one final df for plotting
  finaldf = Reduce(function(...) merge(..., all=T,by = 'hour'), listdf)
  
  finalmelt = melt(finaldf,id = 'hour')
  names(finalmelt)[names(finalmelt)=="variable"] = "Clusters"
  plt3 = ggplot(data=finalmelt,
                aes(x=hour, y=value, colour=Clusters)) +
    geom_line(size=2)+
    theme_classic()+   theme(panel.background = element_rect(fill = "black"))+
    xlab("Hours of a day")+
    ylab("Frequency of tweets")+
    ggtitle("Difference in clusters' time for tweeting - Hourly - Removed outliers")+
    scale_x_continuous(breaks = seq(0,24,1))
  #scale_y_continuous(breaks = seq(0,520,25))
  
  grid.arrange(plt1,plt2,ncol=1, nrow = 2)
  print(plt1)
  print(plt2)
  hourclusters = combineddf
  return(list(hourclusters,cdf))
}





#sink all the ANOVA and Tukey stuff
sink('/Users/gautamborgohain/Desktop/output.txt', append = F)

# Run script for Weekdays  
data = r_agg_wday
cluster = 3
userid_weekday_cluster = clusterAnlaysisOfWeekdays(data,cluster,sample_releasedata,T)

# Run script for Hours
data = r_agg_hr
cluster = 4
userid_hour_cluster = clusterAnlaysisOfHours(data,cluster,sample_releasedata,T)


hourclusters = data.frame(userid_hour_cluster[2])
weekdaycluster = data.frame(userid_weekday_cluster[2])
clusterdf = data.frame(ClusterByHours = hourclusters$cluster, ClusterByWeek = weekdaycluster$cluster)
clusterdf$ClusterByHours = as.numeric(clusterdf$ClusterByHours)
clusterdf$ClusterByWeek = as.numeric(clusterdf$ClusterByWeek)
clusterdf$ClusterByHours[clusterdf$ClusterByHours == 1] <- "Early morning - All day - Late night"
clusterdf$ClusterByHours[clusterdf$ClusterByHours == 2] <- "Afternoon - Late night"
clusterdf$ClusterByHours[clusterdf$ClusterByHours == 3] <- "Lunch Break - After Work"
clusterdf$ClusterByHours[clusterdf$ClusterByHours == 4] <- "Before Breakfast - After Dinner"

clusterdf$ClusterByWeek[clusterdf$ClusterByWeek == 1] <- "All week user"
clusterdf$ClusterByWeek[clusterdf$ClusterByWeek == 2] <- "Weekends user"
clusterdf$ClusterByWeek[clusterdf$ClusterByWeek == 3] <- "Mid Week user"

tbl = table(clusterdf)
tbl
chisq.test(tbl)

sink()# end outputting to the sink

tweetsdf = read.csv('/Users/gautamborgohain/Desktop/DATA/datacombined.csv', header = T)
timeingdf = tweetsdf[c("Created.At","ID")]

