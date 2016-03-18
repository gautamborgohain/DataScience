library(data.table)
library(lubridate)
library(psych)
library(ggplot2)
library(reshape2)
library(gridExtra)
# Function to read the data and process return a data frame ready for processing
readData = function (name = "Politics") {

  if(name == "Politics"){
    mydata = read.csv('/Users/gautamborgohain/Downloads/trump+clinton+cruz+sanders+carsoniowa.csv', skip = 4, stringsAsFactors = F)
  }else if(name == "Movies"){
    mydata = read.csv('/Users/gautamborgohain/Downloads/Batman+CA+Xmen.csv', skip = 4, stringsAsFactors = F)
  }else if(name == "Terror"){
    mydata = read.csv('/Users/gautamborgohain/Downloads/ISIS+Iraq+Syria+terrorism.csv', skip = 4, stringsAsFactors = F)
  }else{
    return(0)
  }
  mydata = mydata[1:109,]
  
  for(colnum in 2:length(names(mydata))){
      mydata[,colnum] = as.numeric(mydata[,colnum])
  }
  #split the week column
  setDT(mydata)[, paste0("Day", 1:2) := tstrsplit(Week, " - ")]
  
  #prepare the dates
  mydata$Day1 = ymd(mydata$Day1)
  mydata$Day2 = ymd(mydata$Day2)
  mydata$week = week(mydata$Day1)
  mydata$month = month(mydata$Day1)
  mydata = data.frame(mydata)
  mydata = mydata[-1]
  return(mydata)
}


#read the topics that are required and create seperate data frames for each
list = c("Movies","Politics","Terror")
for(name in list){
  temp = readData(name)
  assign(name,temp)
  nocolumns = ncol(temp)
  temp = temp[c(nocolumns-4:nocolumns)]#ommit the last 4 columns that have the temporal info
  assign(paste(name,"_1"),temp)
}

#Join the three data frames
combineddf = merge(Movies,Politics)
combineddf = merge(combineddf,Terror)

combineddf_1 = combineddf[-c(1:4)]


#Examine correlation

#Correlation table
Movies.cor <- lowerCor(`Movies _1`)
Politics.cor <- lowerCor(`Politics _1`)
Terror.cor <- lowerCor(`Terror _1`)

#Correlation plots
cor.plot(Movies.cor)
cor.plot(Politics.cor)
cor.plot(Terror.cor)

pairs.panels(`Movies _1`)
pairs.panels(`Politics _1`)
pairs.panels(`Terror _1`)

combineddf_1.cor = lowerCor(combineddf_1)
cor.plot(combineddf_1.cor)
pairs.panels(combineddf_1)


#Examine Temporal growth

combineddf_2 = combineddf[-c(2:4)]
politicsdf = combineddf_2[c(1,5:8)]
moviesdf = combineddf_2[c(1,2:4)]
terrorsdf = combineddf_2[c(1,9:12)]

#Politics
newdf<-melt(politicsdf,'Day1')
names(newdf)[names(newdf)=="variable"]<-"Interest"
politics.plot = ggplot(newdf,aes(x = Day1,y = value,group = Interest,color = Interest)) + 
   geom_line(size=2)+
  geom_text(aes(label=ifelse(value>50,as.character(paste("Date:",format(Day1,"%d-%b-%y")," Hits:",value)),'')),hjust=1,vjust=1) +
  xlab("Week") + 
  ylab("Interest") + 
  ggtitle("Political Candidates interest - USA - Iowa") +
  scale_x_datetime(date_breaks = "1 week", date_labels = "%W") + 
  scale_y_continuous(breaks = seq(0,100,5))+
  theme_bw()+
  theme(legend.title = element_text(face ="italic"))+
  theme(plot.title = element_text(face = "bold",size = 10))+
  theme(legend.position = c(0.1, 0.75))
#Movies
newdf<-melt(moviesdf,'Day1')
names(newdf)[names(newdf)=="variable"]<-"Interest"
movies.plot = ggplot(newdf,aes(x = Day1,y = value,group = Interest,color = Interest)) + 
   geom_line(size=2)+
  geom_text(aes(label=ifelse(value>40,as.character(paste("Date:",format(Day1,"%d-%b-%y")," Hits:",value)),'')),hjust=1,vjust=1) +
  xlab("Week") + 
  ylab("Interest") + 
  ggtitle("Hollywood blockbusters anticipation - 2016 - USA") +
  scale_x_datetime(date_breaks = "1 week", date_labels = "%W") + 
  scale_y_continuous(breaks = seq(0,100,5))+
  theme_bw()+
  theme(legend.title = element_text(face ="italic"))+
  theme(plot.title = element_text(face = "bold",size = 10))+
  theme(legend.position = c(0.1, 0.8))
#Terror
newdf<-melt(terrorsdf,'Day1')
names(newdf)[names(newdf)=="variable"]<-"Interest"
terror.plot = ggplot(newdf,aes(x = Day1,y = value,group = Interest,color = Interest)) + 
   geom_line(size=2)+
  geom_text(aes(label=ifelse(value>35,as.character(paste("Date:",format(Day1,"%d-%b-%y")," Hits:",value)),'')),hjust=1,vjust=1) +
  xlab("Week") + 
  ylab("Interest") + 
  ggtitle("Interest on Terrorism - India") +
  scale_x_datetime(date_breaks = "1 week", date_labels = "%W") + 
  scale_y_continuous(breaks = seq(0,100,5))+
  theme_bw()+
  theme(legend.title = element_text(face ="italic"))+
  theme(plot.title = element_text(face = "bold",size = 10))+
  theme(legend.position = c(0.1, 0.7))

grid.arrange(politics.plot,movies.plot,terror.plot,ncol=1, nrow = 3)


# theme(panel.background = element_rect(fill = "black")) +
#   theme(panel.grid.major.y = element_blank(), panel.grid.minor.y = element_blank()) + 
#   theme(panel.grid.major.x = element_blank(), panel.grid.minor.x = element_blank()) +


