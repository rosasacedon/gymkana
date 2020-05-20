#!/usr/bin/python3 -us


from socket import *
import http.client, struct, time


direccion = 'atclab.esi.uclm.es'
puerto_proxy = 80 
parentesis={'(': ')', '[': ']', '{': '}'}

def cksum(data):

	def sum16(data):
		"sum all the the 16-bit words in data"
		if len(data) % 2:
			data += '\0'.encode()

		return sum(struct.unpack("!%sH" % (len(data) // 2), data))

	retval = sum16(data)                       
	retval = sum16(struct.pack('!L', retval))  
	retval = (retval & 0xFFFF) ^ 0xFFFF        
	return retval

def balanceoCorrecto(data):
	abiertos=0
	pos=0
	cerrados=0
	while pos < len(data):
		caracter=data[pos]
		if(caracter=='(' or caracter=='[' or caracter=='{'):
			abiertos+=1
		if(caracter==')' or caracter==']' or caracter=='}'):
			cerrados+=1
		pos+=1
	return abiertos==cerrados


def getTipooperacion(data):
	pos=0
	pos_numero=0
	operandos=[]
	abiertos=0
	cerrados=0
	while pos < len(data):
		caracter=data[pos]
		subcadena=""
		pos+=1
		if caracter.isdigit():
			if len(operandos)>0 and operandos[pos_numero-1].isdigit():
				operandos[pos_numero-1]+=caracter
			else:
				operandos.append(caracter)
				pos_numero+=1
		elif(caracter=='*' or caracter=='/' or caracter=='+' or caracter=='-'):
			pos_numero+=1
			operandos.append(caracter)
		elif(caracter=='(' or caracter=='[' or caracter=='{'):
			abiertos+=1
			cerrados+=0
			abierto=caracter
			cerrado=parentesis.get(caracter)
			caracter=data[pos]
			while abiertos!=cerrados:
				subcadena+=caracter
				pos+=1
				if(caracter==abierto):
					abiertos+=1
				if(caracter==cerrado):
					cerrados+=1
				if pos<len(data):
					caracter=data[pos]

			operandos.append(getTipooperacion(subcadena))
			pos_numero+=1
	resultado=evalExpresion(operandos)
	return resultado

def evalExpresion(operandos):
	numero = 0
	resultado=[]
	i=0
	while i<len(operandos): 
		if (not operandos[i]=='*' and not operandos[i]=='/' and not operandos[i]=='+' and not operandos[i]=='-'): 
			numero=int(operandos[i]) 
			resultado.append(numero) 
		elif (operandos[i]=='*' or operandos[i]=='/' or operandos[i]=='+' or operandos[i]=='-'): 
			operador=operandos[i] 
			i+=1
			if operador=='*':
				numero*=int(operandos[i])
				resultado.append(numero)
			if operador=='/':
				numero//=int(operandos[i])
				resultado.append(numero)
			if operador=='+' or operador=='-':
				resultado.append(operador)
				numero=int(operandos[i])
				resultado.append(numero)
		i+=1
	i=0
	while i<len(resultado):
		if (not resultado[i]=='*' and not resultado[i]=='/' and not resultado[i]=='+' and not resultado[i]=='-'):
			numero=int(resultado[i])
		else:
			operador=resultado[i]
			i+=1
			if operador=='-':
				numero-=int(resultado[i])
			if operador=='+':
				numero+=int(resultado[i])
		i+=1
	return numero
		

def etapa0TCP():
	tcpSocket = socket(AF_INET,SOCK_STREAM) 
	tcpSocket.connect((direccion, 2000)) 
	datos = (tcpSocket.recv(1024)).decode('utf-8') 
	tcpSocket.close() 
	return (datos) 

def etapa1UDP(identificador):
	udpSocket = socket(AF_INET, SOCK_DGRAM)
	udpSocket.bind(('',2000)) 
	data = ((identificador+" "+str(2000)).encode())
	udpSocket.sendto(data, (direccion, 2000))  
	msg, client = udpSocket.recvfrom(1024) 
	mensaje = msg.decode('utf-8') 
	udpSocket.close() 
	return mensaje 

def etapa2Balanceo(puerto_servidor):
	fase2=True
	datos=""
	sock_tcp = socket(AF_INET, SOCK_STREAM) 
	sock_tcp.connect((direccion, int(puerto_servidor))) 
	while fase2==True: 
		datos=sock_tcp.recv(1024).decode('utf-8') 
		caracter=datos[0]
		if(caracter!='(' and caracter!='[' and caracter!='{'): 
			sock_tcp.close() 
			fase2=False 
		else:
			while balanceoCorrecto(datos)==False: 
				datos_recuperados=sock_tcp.recv(1024).decode('utf-8')
				datos+=datos_recuperados 
				
			resultado="(" + str(getTipooperacion(datos)) + ")" 
			sock_tcp.send(resultado.encode()) 
	return datos

def etapa3Fichero(archivo):
	
	conexion=http.client.HTTPConnection(direccion, 5000) 
	conexion.request("GET","/"+archivo,"") 
	respuesta=conexion.getresponse()
	data=respuesta.read().decode() 
	print(data)
	conexion.close()
	return data


def etapa4ICMP(id):
	
	checksum = 0
	ICMP_ECHO = 8
	Id = 2015
	Sequence = 0
	cabecera = struct.pack("!bbHhh", ICMP_ECHO, 0, checksum, Id, Sequence) 

	data = str(time.clock()) + id 
	checksum = cksum(cabecera + bytes(data, 'ascii'))
	cabecera = struct.pack("!bbHhh", ICMP_ECHO, 0, checksum, Id, Sequence) 
	paquete = cabecera + bytes(data, 'ascii') 
	Socket_RAW = socket(AF_INET, SOCK_RAW,IPPROTO_ICMP) 
	Socket_RAW.sendto(paquete, (direccion, 32)) 
	mensaje = Socket_RAW.recv(512) 
	mensaje = Socket_RAW.recv(2048)[28:]
	print (mensaje.decode())
	Socket_RAW.close()
	return (mensaje.decode())


etapa1=etapa0TCP()[0:5]
etapa2=etapa1UDP(etapa1)[0:5]
etapa3=etapa2Balanceo(etapa2)[0:5]
etapa4=etapa3Fichero(etapa3)[0:5]
etapa4ICMP(etapa4)
